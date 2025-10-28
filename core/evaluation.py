"""Core evaluation engine supporting multiple scale types."""

from typing import Any, Dict, List, Optional, Union
from loguru import logger
import yaml
import asyncio
import os
from pathlib import Path

from models.schemas import (
    AggregationStrategy,
    MissingStrategy,
    ScaleType,
    SelectionStrategy,
)


class EvaluationEngine:
    """Core engine for text evaluation using various scale types."""
    
    def __init__(self, schemes_dir: str = "schemes"):
        self.schemes_dir = Path(schemes_dir)
        self.schemes: Dict[str, Dict[str, Any]] = {}
        self.max_concurrent_llm_calls = int(os.getenv("MAX_CONCURRENT_LLM_CALLS", "20"))
        logger.info(f"Concurrency limit: {self.max_concurrent_llm_calls} parallel LLM calls")
        self._load_schemes()
    
    def _load_schemes(self) -> None:
        """Load all YAML schemes from directory."""
        if not self.schemes_dir.exists():
            logger.warning(f"Schemes directory {self.schemes_dir} not found")
            return
        
        for yaml_file in self.schemes_dir.glob("*.yaml"):
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    scheme = yaml.safe_load(f)
                    self.schemes[scheme['id']] = scheme
                    logger.debug(f"Loaded scheme: {scheme['id']}")
            except Exception as e:
                logger.error(f"Failed to load scheme {yaml_file}: {e}")
        logger.info(
            f"Loaded {len(self.schemes)} schemes from {self.schemes_dir.resolve()}"
        )
    
    def get_schemes(self) -> List[Dict[str, Any]]:
        """Get list of available schemes."""
        return [
            {
                "id": scheme["id"],
                "name": scheme["name"],
                "description": scheme["description"],
                "dimension": scheme["dimension"],
                "scale_type": scheme["type"],
                "output_range": scheme.get("output_range", {}),
                "version": scheme.get("version", "1.0")
            }
            for scheme in self.schemes.values()
        ]
    
    async def _run_with_concurrency_limit(
        self,
        tasks: List[asyncio.Task],
        semaphore: Optional[asyncio.Semaphore] = None
    ) -> List[Any]:
        """
        Run tasks with concurrency limit using a semaphore.
        
        Args:
            tasks: List of asyncio tasks to execute
            semaphore: Optional semaphore for limiting concurrency
            
        Returns:
            List of results in the same order as input tasks
        """
        if semaphore is None:
            semaphore = asyncio.Semaphore(self.max_concurrent_llm_calls)
        
        async def run_with_semaphore(task):
            async with semaphore:
                return await task
        
        # Wrap all tasks with semaphore
        limited_tasks = [run_with_semaphore(task) for task in tasks]
        
        # Execute all tasks (semaphore limits actual concurrency)
        return await asyncio.gather(*limited_tasks, return_exceptions=True)
    
    async def evaluate_text(
        self,
        text: str,
        scheme_ids: List[str],
        llm_client: Any,
        model: str,
        gates_passed: bool = True,
        context_type: str = "content"
    ) -> Dict[str, Any]:
        """Evaluate text using specified schemes.
        
        Uses request-scoped caching to avoid duplicate evaluations when:
        - A scheme appears both directly and as a dependency
        - Multiple derived schemas share the same dependency
        """
        results = []
        gates_passed = True
        
        # Request-scoped cache: scheme_id -> evaluation result
        # This prevents duplicate LLM calls for the same schema
        results_cache: Dict[str, Dict[str, Any]] = {}
        
        # Process binary gates first
        for scheme_id in scheme_ids:
            scheme = self.schemes.get(scheme_id)
            if not scheme:
                continue

            try:
                scheme_type = ScaleType(scheme["type"])
            except (KeyError, ValueError):
                logger.warning(f"Unknown scheme type for {scheme_id}: {scheme.get('type')}")
                continue

            if scheme_type is ScaleType.BINARY_GATE:
                # Check cache first
                if scheme_id in results_cache:
                    result = results_cache[scheme_id]
                    logger.debug(f"Using cached result for {scheme_id}")
                else:
                    result = await self._evaluate_binary_gate(text, scheme, llm_client, model, context_type)
                    results_cache[scheme_id] = result
                results.append(result)
                if result["value"] is False:
                    gates_passed = False
                    break
        
        # If gates failed, return early
        if not gates_passed:
            return {
                "results": results,
                "gates_passed": False,
                "overall_score": None,
                "overall_label": "REJECTED"
            }
        
        # Process other scale types in parallel
        eval_tasks = []
        scheme_order = []  # Track order for maintaining result sequence
        
        for scheme_id in scheme_ids:
            scheme = self.schemes.get(scheme_id)
            if not scheme:
                continue

            try:
                scheme_type = ScaleType(scheme["type"])
            except (KeyError, ValueError):
                logger.warning(f"Unknown scheme type for {scheme_id}: {scheme.get('type')}")
                continue

            if scheme_type is ScaleType.BINARY_GATE:
                continue
            
            scheme_order.append(scheme_id)
            
            # Check cache first - avoid duplicate evaluation
            if scheme_id in results_cache:
                logger.debug(f"Using cached result for {scheme_id}")
                results.append(results_cache[scheme_id])
                continue
            
            if scheme_type is ScaleType.ORDINAL_RUBRIC:
                eval_tasks.append(self._evaluate_ordinal_rubric(text, scheme, llm_client, model))
            elif scheme_type is ScaleType.CHECKLIST_ADDITIVE:
                eval_tasks.append(self._evaluate_checklist_additive(text, scheme, llm_client, model))
            elif scheme_type is ScaleType.DERIVED:
                eval_tasks.append(self._evaluate_derived(text, scheme, llm_client, model, context_type, results_cache))
        
        # Execute all evaluations in parallel (with concurrency limit)
        if eval_tasks:
            parallel_results = await self._run_with_concurrency_limit(eval_tasks)
            
            # Handle results and potential exceptions
            for i, result in enumerate(parallel_results):
                scheme_id = scheme_order[i]
                # Skip if already added from cache
                if scheme_id in results_cache:
                    continue
                    
                if isinstance(result, Exception):
                    logger.error(f"Evaluation failed for {scheme_id}: {result}")
                    result_dict = {
                        "scheme_id": scheme_id,
                        "dimension": "unknown",
                        "value": None,
                        "na_reason": f"Evaluation error: {str(result)}"
                    }
                    results.append(result_dict)
                    results_cache[scheme_id] = result_dict
                else:
                    results.append(result)
                    results_cache[scheme_id] = result
        
        # Calculate overall metrics
        overall_score, overall_label = self._calculate_overall(results)
        
        return {
            "results": results,
            "gates_passed": gates_passed,
            "overall_score": overall_score,
            "overall_label": overall_label
        }
    
    async def _evaluate_binary_gate(
        self,
        text: str,
        scheme: Dict[str, Any],
        llm_client: Any,
        model: str,
        context_type: str = "content",
    ) -> Dict[str, Any]:
        """Evaluate binary gate (KO criteria)."""
        prompt = self._build_gate_prompt(text, scheme, context_type)
        
        try:
            response = await llm_client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            content = response.choices[0].message.content
            
            # Parse structured response
            passed = None
            reasoning = "No evaluation found"
            
            for line in content.split('\n'):
                if line.strip().startswith('RESULT:'):
                    result_part = line.split(':', 1)[1].strip().upper()
                    passed = result_part in ['JA', 'YES', 'TRUE']
                elif line.strip().startswith('REASONING:'):
                    reasoning = line.split(':', 1)[1].strip()
            
            # Calculate overall pass/fail based on individual aspects
            gate_rules = scheme.get('gate_rules', [])
            all_aspects_passed = True
            
            if gate_rules:
                for i, rule in enumerate(gate_rules, 1):
                    # Look for ASPEKT_X pattern in response
                    for line in content.split('\n'):
                        if line.strip().startswith(f'ASPEKT_{i}:'):
                            parts = line.split(':', 1)[1].strip()
                            response_part = parts.split(' - ')[0] if ' - ' in parts else parts
                            # NEIN = kein Verstoß = BESTANDEN (inverted logic for gates)
                            aspect_passed = response_part.strip().upper() in ['NEIN', 'NO', 'FALSE']
                            if not aspect_passed:
                                all_aspects_passed = False
                            break
                
                passed = all_aspects_passed
            else:
                # Fallback parsing for overall result
                if passed is None:
                    content_lower = content.lower()
                    passed = "ja" in content_lower or "yes" in content_lower or "true" in content_lower
            
            reasoning = content.strip()
            
            # Parse individual aspects from gate rules
            gate_rules = scheme.get('gate_rules', [])
            criteria_results = {}
            
            if gate_rules:
                for i, rule in enumerate(gate_rules, 1):
                    aspect_key = f"aspekt_{i}"
                    aspect_passed = True  # Default to pass
                    aspect_reasoning = "Keine spezifische Bewertung gefunden"
                    
                    # Look for ASPEKT_X pattern in response
                    for line in content.split('\n'):
                        if line.strip().startswith(f'ASPEKT_{i}:'):
                            parts = line.split(':', 1)[1].strip()
                            if ' - ' in parts:
                                response_part, aspect_reasoning = parts.split(' - ', 1)
                                # NEIN = kein Verstoß = BESTANDEN (inverted logic for gates)
                                aspect_passed = response_part.strip().upper() in ['NEIN', 'NO', 'FALSE']
                            break
                    
                    criteria_results[aspect_key] = {
                        "passed": aspect_passed,
                        "reasoning": aspect_reasoning,
                        "rule": rule.get('description', 'Unbekannter Aspekt'),
                        "severity": rule.get('severity', 'unbekannt'),
                        "legal_basis": rule.get('legal_basis'),
                        "action": rule.get('action'),
                        "rule_id": rule.get('id')
                    }
            
            # Enhanced reasoning for binary gates - extract only main reasoning
            main_reasoning = ""
            if "REASONING:" in reasoning:
                # Extract the first REASONING section only
                reasoning_parts = reasoning.split("REASONING:")
                if len(reasoning_parts) > 1:
                    main_reasoning = reasoning_parts[1].split("\n")[0].strip()
            
            if not main_reasoning:
                # Fallback to simple reasoning
                sentences = reasoning.replace("\n", " ").split(". ")
                main_reasoning = ". ".join(sentences[:2]) + "." if sentences else "Bewertung durchgeführt."
            
            enhanced_reasoning = f"**Ergebnis:** {'BESTANDEN' if passed else 'NICHT BESTANDEN'}\n\n**Begründung:** {main_reasoning}"
            
            # Collect legal violations for failed gates
            legal_violations = []
            if not passed and gate_rules:
                for i, rule in enumerate(gate_rules, 1):
                    aspect_key = f"aspekt_{i}"
                    if aspect_key in criteria_results and not criteria_results[aspect_key].get('passed', True):
                        violation = {
                            "rule_id": rule.get('id'),
                            "description": rule.get('description'),
                            "legal_basis": rule.get('legal_basis'),
                            "action": rule.get('action')
                        }
                        legal_violations.append(violation)
            
            return {
                "scheme_id": scheme["id"],
                "dimension": scheme["dimension"],
                "value": 1 if passed else 0,
                "label": "PASS" if passed else "FAIL",
                "reasoning": enhanced_reasoning,
                "criteria": criteria_results if criteria_results else None,
                "scale_info": {
                    "type": "binary_gate",
                    "description": scheme.get("description", ""),
                    "criteria": scheme.get("criteria", ""),
                    "total_aspects": len(gate_rules),
                    "legal_violations": legal_violations if legal_violations else None
                },
                "confidence": 0.9 if passed is not None else 0.6
            }
        except Exception as e:
            logger.error(f"Binary gate evaluation failed: {e}")
            return {
                "scheme_id": scheme["id"],
                "dimension": scheme["dimension"],
                "value": None,
                "na_reason": f"Evaluation error: {str(e)}"
            }
    
    async def _evaluate_ordinal_rubric(
        self,
        text: str,
        scheme: Dict[str, Any],
        llm_client: Any,
        model: str,
    ) -> Dict[str, Any]:
        """Evaluate using ordinal rubric with anchors."""
        prompt = self._build_rubric_prompt(text, scheme)
        
        try:
            response = await llm_client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2
            )
            
            content = response.choices[0].message.content
            
            # Parse structured response
            score = None
            label = None
            reasoning = "No evaluation found"
            
            for line in content.split('\n'):
                if line.strip().startswith('SCORE:'):
                    try:
                        score = int(line.split(':', 1)[1].strip())
                    except ValueError:
                        pass
                elif line.strip().startswith('LABEL:'):
                    label = line.split(':', 1)[1].strip()
                elif line.strip().startswith('REASONING:'):
                    reasoning = line.split(':', 1)[1].strip()
            
            # Fallback to anchor matching if structured parsing failed
            if score is None:
                if scheme.get("selection_strategy") == SelectionStrategy.FIRST_MATCH:
                    result = self._match_first_anchor(content, scheme)
                else:
                    result = self._match_best_anchor(content, scheme)
                score = result.get("value")
                label = result.get("label")
                reasoning = content.strip()
            
            # Find matching anchor for label if not parsed
            if label is None and score is not None:
                for anchor in scheme.get('anchors', []):
                    if anchor['value'] == score:
                        label = anchor['label']
                        break
            
            # Enhanced reasoning for ordinal rubrics
            enhanced_reasoning = f"**Bewertung:** Level {score} - {label}\n\n**Begründung:** {reasoning}"
            
            return {
                "scheme_id": scheme["id"],
                "dimension": scheme["dimension"],
                "value": score,
                "label": label or "Unknown",
                "reasoning": enhanced_reasoning,
                "scale_info": {
                    "type": "ordinal_rubric",
                    "range": scheme.get("output_range", {}),
                    "anchors": len(scheme.get('anchors', [])),
                    "levels": [f"{a['value']}: {a['label']}" for a in scheme.get('anchors', [])]
                },
                "confidence": 0.8 if score is not None else 0.6
            }
            
        except Exception as e:
            logger.error(f"Ordinal rubric evaluation failed: {e}")
            return {
                "scheme_id": scheme["id"],
                "dimension": scheme["dimension"],
                "value": None,
                "na_reason": f"Evaluation error: {str(e)}"
            }
    
    async def _evaluate_checklist_additive(
        self,
        text: str,
        scheme: Dict[str, Any],
        llm_client: Any,
        model: str,
    ) -> Dict[str, Any]:
        """Evaluate using additive checklist."""
        prompt = self._build_checklist_prompt(text, scheme)
        
        try:
            response = await llm_client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            content = response.choices[0].message.content
            
            # Parse checklist responses and calculate weighted score
            score, criterion_results = self._calculate_checklist_score(content, scheme)
            
            # Generate detailed LLM reasoning
            reasoning_prompt = f"""
Erstellen Sie eine ausführliche Bewertung für die Dimension '{scheme.get('dimension', 'quality')}' basierend auf folgenden Einzelkriterien:

{chr(10).join([f"- {item.get('prompt', item.get('id', ''))}: Level {criterion_results.get(item.get('id', ''), {}).get('response', 'unbekannt')}" for item in scheme.get('items', [])])}

Gesamtscore: {score:.2f} von {scheme.get('aggregator', {}).get('params', {}).get('scale_factor', 5.0)}

Erstellen Sie eine zusammenhängende, ausführliche Bewertung (2-3 Sätze), die die wichtigsten Stärken und Schwächen erklärt.
"""
            
            try:
                reasoning_response = await llm_client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": reasoning_prompt}],
                    temperature=0.3
                )
                detailed_reasoning = reasoning_response.choices[0].message.content.strip()
            except Exception:
                # Fallback to simple reasoning
                percentage = (score / scheme.get('aggregator', {}).get('params', {}).get('scale_factor', 5.0)) * 100
                dimension_name = scheme.get('dimension', 'quality').title()
                detailed_reasoning = f"Bewertung für {dimension_name}: {percentage:.0f}% der möglichen Punkte erreicht."
            
            # Build scale info from first item's values
            first_item = scheme.get('items', [{}])[0] if scheme.get('items') else {}
            scale_factor = scheme.get('aggregator', {}).get('params', {}).get('scale_factor', 1.0)
            raw_values = first_item.get('values', {})
            
            # Convert values to proper format for scale_info
            scale_values = {}
            for k, v in raw_values.items():
                if k == "na":
                    scale_values["na"] = None
                else:
                    scale_values[str(k)] = v
            
            return {
                "scheme_id": scheme["id"],
                "dimension": scheme["dimension"],
                "value": round(score, 2),
                "label": self._score_to_label(score, scheme),
                "confidence": 0.8,
                "reasoning": detailed_reasoning,
                "scale_info": {
                    "raw_range": "0.0-1.0",
                    "normalized_range": f"0.0-{scale_factor}",
                    "values": scale_values
                },
                "criteria": criterion_results
            }
            
        except Exception as e:
            logger.error(f"Checklist evaluation failed: {e}")
            return {
                "scheme_id": scheme["id"],
                "dimension": scheme["dimension"],
                "value": None,
                "na_reason": f"Evaluation error: {str(e)}"
            }
    
    async def _evaluate_derived(
        self,
        text: str,
        scheme: Dict[str, Any],
        llm_client: Any,
        model: str,
        context_type: str = "content",
        results_cache: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Evaluate a derived scheme by aggregating dependency results.

        Reuses cached dependency results within the same request to minimise
        LLM calls. The derivation rules align with the README section
        "Derived Schemes & Aggregation".

        Args:
            results_cache: Request-scoped cache of already evaluated schemas.
        """
        if results_cache is None:
            results_cache = {}
            
        try:
            # Get dependencies and evaluate them first
            dependencies = scheme.get("dependencies", [])
            if not dependencies:
                return {
                    "scheme_id": scheme["id"],
                    "dimension": scheme["dimension"],
                    "value": None,
                    "na_reason": "No dependencies defined"
                }
            
            # Evaluate all dependency schemas
            dependency_tasks = []
            dependency_order = []
            dependency_results = []
            
            for dep_scheme_id in dependencies:
                dep_scheme = self.schemes.get(dep_scheme_id)
                if not dep_scheme:
                    continue
                
                # Check cache first - avoid duplicate evaluation!
                if dep_scheme_id in results_cache:
                    logger.debug(f"Reusing cached dependency: {dep_scheme_id}")
                    dependency_results.append(results_cache[dep_scheme_id])
                    continue
                
                dependency_order.append(dep_scheme_id)
                try:
                    dep_type = ScaleType(dep_scheme["type"])
                except (KeyError, ValueError):
                    logger.warning(
                        f"Unknown dependency scheme type for {dep_scheme_id}: {dep_scheme.get('type')}"
                    )
                    continue

                if dep_type is ScaleType.CHECKLIST_ADDITIVE:
                    dependency_tasks.append(
                        self._evaluate_checklist_additive(text, dep_scheme, llm_client, model)
                    )
                elif dep_type is ScaleType.ORDINAL_RUBRIC:
                    dependency_tasks.append(
                        self._evaluate_ordinal_rubric(text, dep_scheme, llm_client, model)
                    )
                elif dep_type is ScaleType.BINARY_GATE:
                    dependency_tasks.append(
                        self._evaluate_binary_gate(text, dep_scheme, llm_client, model, context_type)
                    )
                elif dep_type is ScaleType.DERIVED:
                    # Recursively evaluate nested derived schemas with cache
                    dependency_tasks.append(
                        self._evaluate_derived(text, dep_scheme, llm_client, model, context_type, results_cache)
                    )

            # Execute all dependency evaluations in parallel (with concurrency limit)
            if dependency_tasks:
                parallel_dep_results = await self._run_with_concurrency_limit(dependency_tasks)
                
                for i, result in enumerate(parallel_dep_results):
                    dep_scheme_id = dependency_order[i]
                    if isinstance(result, Exception):
                        logger.error(f"Dependency evaluation failed for {dep_scheme_id}: {result}")
                        result_dict = {
                            "scheme_id": dep_scheme_id,
                            "dimension": "unknown",
                            "value": None,
                            "na_reason": f"Dependency error: {str(result)}"
                        }
                        dependency_results.append(result_dict)
                        results_cache[dep_scheme_id] = result_dict
                    else:
                        dependency_results.append(result)
                        # Cache the result for potential reuse
                        results_cache[dep_scheme_id] = result
            
            # Apply derivation rules
            rules = scheme.get("rules", [])
            logger.debug(f"Checking {len(rules)} rules for scheme {scheme['id']}")
            logger.debug(
                "Dependency results: {}",
                [
                    (dep.get('scheme_id'), dep.get('dimension'), dep.get('value'))
                    for dep in dependency_results
                ],
            )
            for rule in rules:
                conditions = rule.get("conditions", [])
                logger.debug(f"Checking rule conditions: {conditions}")
                
                conditions_met = self._check_rule_conditions(dependency_results, conditions)
                logger.debug(f"Rule conditions met: {conditions_met}")
                
                if conditions_met:
                    logger.debug(f"Applying rule with value: {rule['value']}")
                    if rule["value"] == "weighted_average":
                        # Calculate weighted average
                        weights = rule.get("weights", {})
                        total_weighted_score = 0
                        total_weight = 0
                        
                        for dep_result in dependency_results:
                            dimension = dep_result.get("dimension")
                            value = dep_result.get("value")
                            weight = weights.get(dimension, 1.0)
                            
                            if value is not None and isinstance(value, (int, float)):
                                total_weighted_score += value * weight
                                total_weight += weight
                        
                        final_score = total_weighted_score / total_weight if total_weight > 0 else 0
                        
                        # Build comprehensive reasoning
                        detailed_reasoning = self._build_derived_reasoning(dependency_results, final_score, weights, rule)
                        
                        return {
                            "scheme_id": scheme["id"],
                            "dimension": scheme["dimension"],
                            "value": round(final_score, 2),
                            "label": self._score_to_label(final_score, scheme),
                            "reasoning": detailed_reasoning,
                            "confidence": rule.get("confidence", 0.9),
                            "scale_info": {
                                "type": "derived",
                                "method": "weighted_average",
                                "dependencies": len(dependencies),
                                "weights": weights
                            },
                            "criteria": {
                                dep["scheme_id"]: {
                                    "dimension": dep["dimension"],
                                    "value": dep.get("value"),
                                    "label": dep.get("label"),
                                    "weight": weights.get(dep.get("dimension"), 1.0),
                                    "confidence": dep.get("confidence"),
                                    "reasoning": dep.get("reasoning"),
                                    "criteria": dep.get("criteria"),
                                    "scale_info": dep.get("scale_info")
                                }
                                for dep in dependency_results if dep.get("value") is not None
                            }
                        }
                    elif rule["value"] == "sum":
                        # Calculate sum of all dependency values (for split schemas)
                        total_sum = 0
                        count = 0
                        
                        for dep_result in dependency_results:
                            value = dep_result.get("value")
                            if value is not None and isinstance(value, (int, float)):
                                total_sum += value
                                count += 1
                        
                        # Build reasoning for sum aggregation
                        reasoning_parts = [f"**Gesamtsumme:** {total_sum:.2f} (aus {count} Teilschemas)\n"]
                        reasoning_parts.append("**Einzelbeiträge:**")
                        for dep in dependency_results:
                            if dep.get("value") is not None:
                                scheme_id = dep.get("scheme_id", "unknown")
                                value = dep.get("value")
                                label = dep.get("label", "")
                                reasoning_parts.append(f"- {scheme_id}: {value} ({label})")
                        
                        reasoning_parts.append(f"\n**Berechnung:** Summe aller Teilwerte = {total_sum:.2f}")
                        detailed_reasoning = "\n".join(reasoning_parts)
                        
                        return {
                            "scheme_id": scheme["id"],
                            "dimension": scheme["dimension"],
                            "value": round(total_sum, 2),
                            "label": self._score_to_label(total_sum, scheme),
                            "reasoning": detailed_reasoning,
                            "confidence": rule.get("confidence", 0.9),
                            "scale_info": {
                                "type": "derived",
                                "method": "sum",
                                "dependencies": len(dependencies),
                                "components": count
                            },
                            "criteria": {
                                dep["scheme_id"]: {
                                    "dimension": dep["dimension"],
                                    "value": dep.get("value"),
                                    "label": dep.get("label"),
                                    "confidence": dep.get("confidence"),
                                    "reasoning": dep.get("reasoning"),
                                    "criteria": dep.get("criteria"),
                                    "scale_info": dep.get("scale_info")
                                }
                                for dep in dependency_results if dep.get("value") is not None
                            }
                        }
                    else:
                        # Static rule value - build detailed reasoning for binary compliance
                        detailed_reasoning = self._build_compliance_reasoning(dependency_results, rule)
                        
                        return {
                            "scheme_id": scheme["id"],
                            "dimension": scheme["dimension"],
                            "value": rule["value"],
                            "label": rule["label"],
                            "reasoning": detailed_reasoning,
                            "confidence": rule.get("confidence", 0.9),
                            "scale_info": {
                                "type": "derived",
                                "method": "rule_based",
                                "dependencies": len(dependencies),
                                "conditions": rule.get("conditions", [])
                            },
                            "criteria": {
                                dep["scheme_id"]: {
                                    "dimension": dep["dimension"],
                                    "value": dep.get("value"),
                                    "label": dep.get("label"),
                                    "passed": dep.get("value") == 1 if isinstance(dep.get("value"), int) else True,
                                    "confidence": dep.get("confidence"),
                                    "reasoning": dep.get("reasoning"),
                                    "criteria": dep.get("criteria"),
                                    "scale_info": dep.get("scale_info")
                                }
                                for dep in dependency_results if dep.get("value") is not None
                            }
                        }
            
            # Default if no rules match - build detailed reasoning for failed compliance
            default = scheme.get("default", {})
            detailed_reasoning = self._build_compliance_reasoning(dependency_results, default)
            
            return {
                "scheme_id": scheme["id"],
                "dimension": scheme["dimension"],
                "value": default.get("value", 0.0),
                "label": default.get("label", "Unbewertet"),
                "reasoning": detailed_reasoning,
                "confidence": default.get("confidence", 0.0),
                "scale_info": {
                    "type": "derived",
                    "method": "rule_based",
                    "dependencies": len(dependencies),
                    "conditions": "default_fallback"
                },
                "criteria": {
                    dep["scheme_id"]: {
                        "dimension": dep["dimension"],
                        "value": dep.get("value"),
                        "label": dep.get("label"),
                        "passed": dep.get("value") == 1 if isinstance(dep.get("value"), int) else True,
                        "confidence": dep.get("confidence"),
                        "reasoning": dep.get("reasoning"),
                        "criteria": dep.get("criteria"),
                        "scale_info": dep.get("scale_info")
                    }
                    for dep in dependency_results if dep.get("value") is not None
                }
            }
            
        except Exception as e:
            logger.error(f"Derived evaluation failed: {e}")
            logger.error(f"Dependencies: {dependencies}")
            logger.error(f"Dependency results: {[{k: v for k, v in dep.items() if k in ['scheme_id', 'dimension', 'value', 'label']} for dep in dependency_results]}")
            return {
                "scheme_id": scheme["id"],
                "dimension": scheme["dimension"],
                "value": None,
                "na_reason": f"Derivation error: {str(e)}"
            }
    
    def _build_derived_reasoning(self, dependency_results, final_score, weights, rule):
        """Build concise reasoning for weighted average derived schemas."""
        summary_lines = []

        for dep in dependency_results:
            if dep.get("value") is None:
                continue

            dimension = dep.get("dimension", "unknown")
            label = dep.get("label", "")
            weight = weights.get(dimension, 1.0)
            sub_reasoning = dep.get("reasoning", "").strip()

            # Extract the most informative fragment from the sub-reasoning
            if sub_reasoning:
                reasoning_lines = [line.strip() for line in sub_reasoning.split("\n") if line.strip()]
                excerpt = reasoning_lines[0]
                if len(reasoning_lines) > 1:
                    excerpt = f"{excerpt} {reasoning_lines[1]}".strip()
            else:
                excerpt = f"Bewertung {label}."

            summary_lines.append(
                f"- **{dimension}** ({label}, Gewicht {weight}): {excerpt}"
            )

        headline = rule.get(
            "reasoning",
            "Aggregation der Teilbereiche basierend auf gewichteten Qualitätsdimensionen"
        )

        return "\n".join([
            f"**Gesamtbewertung:** {final_score:.2f}/5.0 — {headline}",
            "",
            "**Schlüsselbefunde aus den Teilbereichen:**",
            *summary_lines
        ])
    
    def _build_compliance_reasoning(self, dependency_results, rule):
        """Build detailed reasoning for compliance-based derived schemas."""
        passed_count = 0
        failed_count = 0
        failed_gates_details = []
        
        # Count passed/failed and collect details of failed gates
        for dep in dependency_results:
            gate_name = dep.get("scheme_id", "unknown")
            value = dep.get("value")
            label = dep.get("label", "")
            reasoning = dep.get("reasoning", "")
            criteria = dep.get("criteria", {})
            scale_info = dep.get("scale_info", {})
            
            if value == 1:
                passed_count += 1
            else:
                failed_count += 1
                
                # Extract meaningful reasoning from gate
                reasoning_lines = [line.strip() for line in reasoning.split('\n') if line.strip()]
                # Get "Begründung:" section (usually after "**Ergebnis:**")
                begründung_text = ""
                for i, line in enumerate(reasoning_lines):
                    if line.startswith('**Begründung:**'):
                        # Take this line and the next few sentences (up to 3-4 lines)
                        begründung_text = ' '.join(reasoning_lines[i:i+4])
                        break
                
                if not begründung_text and len(reasoning_lines) > 1:
                    # Fallback: take lines after first line
                    begründung_text = ' '.join(reasoning_lines[1:4])
                
                # Clean up markdown formatting
                begründung_text = begründung_text.replace('**Begründung:**', '').replace('**', '').strip()
                
                # Extract failed criteria details for binary gates
                failed_aspects = []
                if criteria and isinstance(criteria, dict):
                    for aspect_key, aspect_data in criteria.items():
                        if isinstance(aspect_data, dict) and not aspect_data.get('passed', True):
                            aspect_reason = aspect_data.get('reasoning', '')
                            if aspect_reason:
                                failed_aspects.append(aspect_reason)
                
                # Extract legal violations from scale_info
                legal_violations = scale_info.get('legal_violations', []) if scale_info else []
                
                # Build structured details
                gate_details = {
                    "name": gate_name,
                    "label": label,
                    "reasoning": begründung_text[:300] if begründung_text else "Keine Begründung verfügbar",
                    "failed_aspects": failed_aspects[:3],  # Max 3 failed aspects
                    "legal_violations": legal_violations,
                    "type": scale_info.get("type", "unknown")
                }
                failed_gates_details.append(gate_details)
        
        reasoning_parts = []
        
        # Summary
        if failed_count > 0:
            reasoning_parts.append(f"**Ergebnis:** {failed_count} von {len(dependency_results)} Prüfungen nicht bestanden")
            reasoning_parts.append(f"\n**Kritische Verstöße:**\n")
            
            # List each failed gate with detailed reasoning
            for gate in failed_gates_details:
                reasoning_parts.append(f"❌ **{gate['name']}** ({gate['label']})")
                reasoning_parts.append(f"   {gate['reasoning']}")
                
                # Add legal violations if available (for binary gates)
                if gate.get('legal_violations'):
                    for violation in gate['legal_violations']:
                        reasoning_parts.append(f"\n   **Verstoß:** {violation.get('rule_id')} - {violation.get('description')}")
                        if violation.get('legal_basis'):
                            reasoning_parts.append(f"   **Rechtsgrundlage:** {violation.get('legal_basis')}")
                        if violation.get('action'):
                            reasoning_parts.append(f"   **Maßnahme:** {violation.get('action')}")
                
                # Add failed aspects if available (for binary gates without legal violations)
                elif gate.get('failed_aspects'):
                    reasoning_parts.append(f"\n   **Fehlgeschlagene Aspekte:**")
                    for aspect in gate['failed_aspects']:
                        reasoning_parts.append(f"   • {aspect}")
                
                reasoning_parts.append("")  # Empty line between gates
            
            reasoning_parts.append(f"**Fazit:** {rule.get('reasoning', 'Compliance nicht erfüllt')}")
        else:
            reasoning_parts.append(f"**Ergebnis:** Alle {len(dependency_results)} rechtlichen Prüfungen bestanden")
            reasoning_parts.append(f"\n**Fazit:** {rule.get('reasoning', 'Volle Compliance erreicht')}")
        
        return "\n".join(reasoning_parts)
    
    def _build_gate_prompt(self, text: str, scheme: Dict[str, Any], context_type: str = "content") -> str:
        """Build prompt for binary gate evaluation.
        
        Args:
            text: Text to evaluate
            scheme: Schema definition
            context_type: Evaluation context - "content" (default), "platform", or "both"
                         "content": Only evaluate content-related rules (UGC, general content)
                         "platform": Evaluate all rules including platform/metadata requirements
                         "both": Evaluate all rules
        """
        # Extract and filter gate rules based on scope
        all_gate_rules = scheme.get('gate_rules', [])
        gate_rules = []
        
        for rule in all_gate_rules:
            rule_scope = rule.get('scope', 'both')  # Default to 'both' if not specified
            
            # Filter rules based on context_type
            if context_type == "content" and rule_scope in ["content", "both"]:
                gate_rules.append(rule)
            elif context_type == "platform":
                gate_rules.append(rule)  # Include all rules for platform evaluation
            elif context_type == "both":
                gate_rules.append(rule)  # Include all rules
        
        rules_text = ""
        if gate_rules:
            rules_text = "\n\n**Prüfen Sie jeden der folgenden Aspekte einzeln:**\n"
            for i, rule in enumerate(gate_rules, 1):
                rule_desc = rule.get('description', 'Unbekannter Aspekt')
                rule_id = rule.get('id', f'Regel-{i}')
                legal_basis = rule.get('legal_basis', 'N/A')
                rule_scope = rule.get('scope', 'both')
                scope_note = f" [Scope: {rule_scope}]" if context_type == "both" else ""
                rules_text += f"\nASPEKT {i} ({rule_id}){scope_note}:\n"
                rules_text += f"  Beschreibung: {rule_desc}\n"
                rules_text += f"  Rechtsgrundlage: {legal_basis}\n"
            
            context_note = ""
            if context_type == "content":
                context_note = "\n**Kontext:** Sie bewerten NUR den Inhalt selbst. Metadaten wie Alterskennzeichnungen, Plattform-Features sind NICHT relevant."
            elif context_type == "platform":
                context_note = "\n**Kontext:** Sie bewerten den Inhalt UND die Plattform/Metadaten (Kennzeichnungen, technische Maßnahmen)."
            
            rules_text += f"{context_note}\n**Bewertungslogik:** Antworten Sie mit NEIN, wenn der Text KEINEN Verstoß enthält (Gate bestanden). Antworten Sie mit JA, wenn ein Verstoß vorliegt (Gate nicht bestanden)."
        
        return f"""
Sie sind ein Experte für {scheme.get('dimension', 'Content Compliance')}.

**Aufgabe:** {scheme['description']}

**Zu prüfender Text:**
{text}

**Prüfkriterien:**
{scheme.get('criteria', 'Prüfen Sie, ob der Inhalt die Gate-Anforderungen erfüllt')}
{rules_text}

**Antwortformat:**

RESULT: [JA/NEIN] (JA = alle Aspekte bestanden, NEIN = mind. ein Verstoß)
REASONING: [Präzise Begründung in 2-3 Sätzen, die auf den konkreten Text Bezug nimmt]

{f"\nFür jeden Aspekt:\nASPEKT_[NUMMER]: [NEIN/JA] - [Konkrete Begründung basierend auf dem Text]\n\n**Wichtig:** NEIN bedeutet 'kein Verstoß' (bestanden), JA bedeutet 'Verstoß festgestellt' (nicht bestanden)." if gate_rules else ""}

**Beispiel:**
RESULT: NEIN
REASONING: Der Text beschreibt eine brutale Kampfszene mit expliziter Gewaltdarstellung, die für die Zielgruppe ungeeignet ist.
{f"ASPEKT_1: JA - Die dargestellte Gewalt überschreitet die Altersfreigabe-Grenzen gemäß JuSchG §14." if gate_rules else ""}
"""
    
    def _build_rubric_prompt(self, text: str, scheme: Dict[str, Any]) -> str:
        """Build prompt for ordinal rubric evaluation."""
        anchors = scheme.get('anchors', [])
        anchors_text = "\n".join([
            f"**Level {anchor['value']}:** {anchor['label']}\n  Beschreibung: {anchor['description']}"
            for anchor in anchors
        ])
        
        return f"""
Sie sind ein Experte für {scheme.get('dimension', 'Content Evaluation')}.

**Aufgabe:** Bewerten Sie den Text anhand der folgenden Rubrik:

{anchors_text}

**Zu bewertender Text:**
{text}

**Anweisungen:**
1. Lesen Sie den Text sorgfältig
2. Vergleichen Sie ihn mit allen Rubrik-Levels
3. Wählen Sie das Level, das am besten passt
4. Begründen Sie Ihre Wahl präzise mit Bezug zum Text

**Antwortformat:**
SCORE: [Level-Nummer]
LABEL: [Level-Bezeichnung]
REASONING: [Präzise Begründung in 2-3 Sätzen, die auf konkrete Textstellen Bezug nimmt]

**Beispiel:**
SCORE: 2
LABEL: Ausreichend
REASONING: Der Text zeigt einige relevante Aspekte, jedoch fehlt es an Detailtiefe und vollständiger Argumentation.
"""
    
    def _build_checklist_prompt(self, text: str, scheme: Dict[str, Any]) -> str:
        """Build prompt for checklist evaluation."""
        items_text = []
        for i, item in enumerate(scheme.get('items', []), 1):
            item_text = f"\n**Kriterium {i}: {item['id']}** (Gewicht: {item['weight']})\n"
            item_text += f"Frage: {item['prompt']}\n"
            
            # Add scale information from YAML
            values = item.get('values', {})
            if values:
                item_text += "\nBewertungsskala:\n"
                # Filter and sort only numeric keys first
                numeric_items = [(k, v) for k, v in values.items() if isinstance(k, int) and v is not None]
                for level, value_data in sorted(numeric_items):
                    if isinstance(value_data, dict):
                        # New format with score and description
                        score = value_data.get('score', 0)
                        description = value_data.get('description', f'Level {level}')
                        item_text += f"  Level {level} ({score} Punkte): {description}\n"
                    else:
                        # Old format with just numeric value
                        item_text += f"  Level {level}: {value_data} Punkte\n"
            items_text.append(item_text)
        
        return f"""
Sie sind ein Experte für {scheme.get('dimension', 'Content Evaluation')}.

**Aufgabe:** Bewerten Sie den Text systematisch anhand der folgenden Kriterien:

{''.join(items_text)}

**Zu bewertender Text:**
{text}

**Anweisungen:**
1. Bewerten Sie jedes Kriterium einzeln
2. Wählen Sie das passende Level basierend auf dem Text
3. Begründen Sie jede Bewertung präzise

**Antwortformat (für jedes Kriterium):**
[KRITERIUM_ID]: [LEVEL_NUMMER] - [Konkrete Begründung mit Textbezug]

**Beispiel:**
perspektivenvielfalt: 1 - Der Text präsentiert ausschließlich die Regierungsperspektive, alternative Sichtweisen fehlen.
neutrale_beschreibung: 2 - Weitgehend neutral, jedoch mit vereinzelten wertenden Adjektiven wie "umstritten".

**Abschließend:** Geben Sie eine Zusammenfassung der Gesamtbewertung in 2-3 Sätzen.
"""
    
    def _match_first_anchor(self, content: str, scheme: Dict[str, Any]) -> Dict[str, Any]:
        """Match content to first applicable anchor."""
        # Simple keyword matching - could be enhanced with LLM parsing
        for anchor in scheme.get('anchors', []):
            if str(anchor['value']) in content or anchor['label'].lower() in content.lower():
                return {
                    "value": anchor['value'],
                    "label": anchor['label'],
                    "confidence": 0.8
                }
        
        return {"value": None, "na_reason": "No matching anchor found"}
    
    def _match_best_anchor(self, content: str, scheme: Dict[str, Any]) -> Dict[str, Any]:
        """Match content to best fitting anchor."""
        # Placeholder for more sophisticated matching
        return self._match_first_anchor(content, scheme)
    
    def _calculate_checklist_score(
        self, 
        content: str, 
        scheme: Dict[str, Any]
    ) -> tuple[float, Dict[str, Any]]:
        """Calculate weighted score from checklist responses."""
        items = scheme.get('items', [])
        total_weight = 0
        weighted_score = 0
        criterion_results = {}
        
        # Parse structured responses using the new format
        content_lines = content.split('\n')
        
        for item in items:
            weight = item.get('weight', 1.0)
            values = item.get('values', {})
            item_id = item.get('id', '')
            
            # Look for structured format: "item_id: [LEVEL_NUMBER] - reasoning"
            item_score = None
            item_response = "UNCLEAR"
            reasoning = "No evaluation found"
            
            for line in content_lines:
                if line.strip().startswith(f"{item_id}:"):
                    # Parse structured line
                    parts = line.split(':', 1)[1].strip()
                    if ' - ' in parts:
                        response_part, reasoning = parts.split(' - ', 1)
                        response_part = response_part.strip()
                    else:
                        response_part = parts.strip()
                    
                    # Parse numeric level from YAML values
                    try:
                        level = int(response_part)
                        if level in values:
                            item_response = str(level)
                            # Handle both old format (float) and new format (dict with score)
                            value_data = values[level]
                            if isinstance(value_data, dict) and 'score' in value_data:
                                item_score = value_data['score']
                            else:
                                item_score = value_data
                        else:
                            # Fallback to closest valid level
                            valid_levels = [k for k in values.keys() if isinstance(k, int)]
                            if valid_levels:
                                closest_level = min(valid_levels, key=lambda x: abs(int(x) - level))
                                item_response = str(closest_level)
                                # Handle both old format (float) and new format (dict with score)
                                value_data = values[closest_level]
                                if isinstance(value_data, dict) and 'score' in value_data:
                                    item_score = value_data['score']
                                else:
                                    item_score = value_data
                    except ValueError:
                        # Handle non-numeric responses as fallback
                        response_upper = response_part.upper()
                        if response_upper in ['JA', 'YES', 'TRUE']:
                            # Map to highest level
                            int_keys = [k for k in values.keys() if isinstance(k, int)]
                            if int_keys:
                                max_level = max(int_keys)
                                item_response = str(max_level)
                                # Handle both old format (float) and new format (dict with score)
                                value_data = values[max_level]
                                if isinstance(value_data, dict) and 'score' in value_data:
                                    item_score = value_data['score']
                                else:
                                    item_score = value_data
                        elif response_upper in ['NEIN', 'NO', 'FALSE']:
                            # Map to lowest level
                            int_keys = [k for k in values.keys() if isinstance(k, int)]
                            if int_keys:
                                min_level = min(int_keys)
                                item_response = str(min_level)
                                # Handle both old format (float) and new format (dict with score)
                                value_data = values[min_level]
                                if isinstance(value_data, dict) and 'score' in value_data:
                                    item_score = value_data['score']
                                else:
                                    item_score = value_data
                        else:
                            item_response = "UNCLEAR"
                            item_score = values.get('na', 0.5)
                    break
            
            # Fallback parsing if structured format not found
            if item_score is None:
                item_section = ""
                for i, line in enumerate(content_lines):
                    if item_id in line.lower():
                        item_section = '\n'.join(content_lines[i:i+3])
                        break
                
                if item_section:
                    # Try to extract numeric levels from context
                    import re
                    level_matches = re.findall(r'\b([1-4])\b', item_section)
                    
                    if level_matches:
                        # Use first found level
                        level = int(level_matches[0])
                        if level in values:
                            # Handle both old format (float) and new format (dict with score)
                            value_data = values[level]
                            if isinstance(value_data, dict) and 'score' in value_data:
                                item_score = value_data['score']
                            else:
                                item_score = value_data
                            item_response = str(level)
                            reasoning = "Inferred from context"
                    else:
                        # Fallback to sentiment analysis
                        yes_count = item_section.lower().count('yes') + item_section.lower().count('ja')
                        no_count = item_section.lower().count('no') + item_section.lower().count('nein')
                        
                        if no_count > yes_count and no_count > 0:
                            int_keys = [k for k in values.keys() if isinstance(k, int)]
                            if int_keys:
                                min_level = min(int_keys)
                                # Handle both old format (float) and new format (dict with score)
                                value_data = values[min_level]
                                if isinstance(value_data, dict) and 'score' in value_data:
                                    item_score = value_data['score']
                                else:
                                    item_score = value_data
                                item_response = str(min_level)
                                reasoning = "Inferred from context (negative)"
                        elif yes_count > no_count and yes_count > 0:
                            int_keys = [k for k in values.keys() if isinstance(k, int)]
                            if int_keys:
                                max_level = max(int_keys)
                                # Handle both old format (float) and new format (dict with score)
                                value_data = values[max_level]
                                if isinstance(value_data, dict) and 'score' in value_data:
                                    item_score = value_data['score']
                                else:
                                    item_score = value_data
                                item_response = str(max_level)
                                reasoning = "Inferred from context (positive)"
            
            # Store detailed criterion result
            if item_score is not None:
                weighted_score += item_score * weight
                total_weight += weight
                
                # Normalize individual score to output scale for user understanding
                scale_factor = scheme.get('aggregator', {}).get('params', {}).get('scale_factor', 1.0)
                normalized_score = item_score * scale_factor
                
                criterion_results[item_id] = {
                    "name": item.get('prompt', item_id),
                    "response": item_response,
                    "normalized_score": round(normalized_score, 2),
                    "weight": weight,
                    "reasoning": reasoning.strip()
                }
            else:
                # Handle missing evaluation
                missing_strategy = scheme.get('aggregator', {}).get('params', {}).get('missing', 'ignore')
                if missing_strategy != 'ignore':
                    total_weight += weight
                
                criterion_results[item_id] = {
                    "name": item.get('prompt', item_id),
                    "response": "UNCLEAR",
                    "normalized_score": None,
                    "weight": weight,
                    "reasoning": "No evaluation found"
                }
        
        # Calculate weighted average score across all items
        items = scheme.get('items', [])
        total_weighted_score = 0
        total_weight = 0
        
        for item in items:
            item_id = item['id']
            if item_id in criterion_results:
                score = criterion_results[item_id]['normalized_score']
                weight = item.get('weight', 1.0)
                total_weighted_score += score * weight
                total_weight += weight
        
        average_score = total_weighted_score / total_weight if total_weight > 0 else 0
        scale_factor = scheme.get('aggregator', {}).get('params', {}).get('scale_factor', 1.0)
        final_score = average_score
        
        return final_score, criterion_results
    
    def _score_to_label(self, score: float, scheme: Dict[str, Any]) -> str:
        """Convert numeric score to label using German labels from YAML."""
        labels = scheme.get('labels', {})
        if not labels:
            return "Unknown"
        
        # Sort thresholds in descending order and find first match
        try:
            for threshold_str, label in sorted(labels.items(), key=lambda x: float(x[0]), reverse=True):
                threshold = float(threshold_str)
                if score >= threshold:
                    return label
            
            # Fallback to lowest label if score is below all thresholds
            lowest_threshold = min(labels.keys(), key=lambda x: float(x))
            return labels[lowest_threshold]
        except (ValueError, TypeError) as e:
            # Handle any conversion errors
            return "Unknown"
    
    def _check_rule_conditions(
        self, 
        results: List[Dict[str, Any]], 
        conditions: List[Dict[str, Any]]
    ) -> bool:
        """Check if derivation rule conditions are met."""
        for condition in conditions:
            dimension = condition.get('dimension')
            operator = condition.get('operator', '>=')
            threshold = condition.get('value')
            
            result = next((r for r in results if r.get('dimension') == dimension), None)
            if not result or result.get('value') is None:
                return False
            
            value = result['value']
            if operator == '>=' and value >= threshold:
                continue
            elif operator == '>' and value > threshold:
                continue
            elif operator == '<=' and value <= threshold:
                continue
            elif operator == '<' and value < threshold:
                continue
            elif operator == '==' and value == threshold:
                continue
            else:
                return False
        
        return True
    
    def _calculate_overall(self, results: List[Dict[str, Any]]) -> tuple[Optional[float], Optional[str]]:
        """Calculate overall score and label from non-binary evaluation results."""
        valid_results: List[tuple[Dict[str, Any], Dict[str, Any]]] = []
        for result in results:
            value = result.get('value')
            if value is None or not isinstance(value, (int, float)):
                continue

            scheme = self.schemes.get(result.get('scheme_id'))
            if not scheme:
                continue

            try:
                scheme_type = ScaleType(scheme['type'])
            except (KeyError, ValueError):
                continue

            if scheme_type is ScaleType.BINARY_GATE:
                # Binary gate outcomes are not averaged into overall scores
                continue

            valid_results.append((result, scheme))

        if not valid_results:
            return None, None

        overall_score = sum(result['value'] for result, _ in valid_results) / len(valid_results)

        # Use label from first scheme's YAML labels
        _, reference_scheme = valid_results[0]
        overall_label = self._score_to_label(overall_score, reference_scheme)

        return overall_score, overall_label

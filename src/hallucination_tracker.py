"""
Hallucination Tracker - Longitudinal tracking of hallucinations across iterations
Main analysis engine for Student A research
"""

import json
from typing import Dict, List, Optional, Set, Tuple
from collections import defaultdict
import pandas as pd # pyright: ignore[reportMissingModuleSource]
from datetime import datetime

from src.hallucination_taxonomy import (
    HallucinationInstance,
    HallucinationState,
    HallucinationTrajectory,
    HallucinationType,
    Severity,
    get_hallucination_severity,
)

STATES = [s.value for s in HallucinationState]


class HallucinationTracker:
    """
    Tracks hallucinations across multi-turn coding sessions.
    Computes persistence rates, mutation patterns, and propagation flows.
    """

    def __init__(self, corpus_id: str):
        self.corpus_id = corpus_id
        self.trajectories: Dict = {}
        self.task_trajectories: Dict = defaultdict(list)
        self.hallucinations_by_type: Dict = defaultdict(list)

    # ------------------------------------------------------------------
    # Loading data
    # ------------------------------------------------------------------

    def add_trajectory(self, trajectory: HallucinationTrajectory):
        """Register a hallucination trajectory"""
        self.trajectories[trajectory.hallucination_id] = trajectory
        self.task_trajectories[trajectory.task_id].append(trajectory)
        halluc_type = self._trajectory_type(trajectory)
        if halluc_type:
            self.hallucinations_by_type[halluc_type].append(trajectory)

    def load_annotations(self, annotations: List[Dict]):
        """
        Build trajectories from manual annotations (see SHAGAI_HERDMAN_PARTA.md 1.2).

        Each annotation is one hallucination occurrence in one iteration. Annotations
        sharing a hallucination_id form one trajectory. An optional "state" field
        (persist/mutate/resolve/masked/compound) labels the occurrence; otherwise the
        first occurrence is PERSIST and later ones are inferred as PERSIST.
        """
        grouped = defaultdict(list)
        for ann in annotations:
            grouped[ann["hallucination_id"]].append(ann)

        for halluc_id, anns in grouped.items():
            anns.sort(key=lambda a: a["iteration"])
            trajectory = HallucinationTrajectory(
                hallucination_id=halluc_id,
                task_id=anns[0]["task_id"],
                instances=[],
                state_transitions=[],
                persistence_duration=0,
                final_state=HallucinationState.PERSIST,
            )
            for ann in anns:
                state = HallucinationState(ann.get("state", "persist"))
                trajectory.add_instance(self._instance_from_dict(ann), state)
                trajectory.final_state = state
            trajectory.persistence_duration = self._duration(trajectory)
            self.add_trajectory(trajectory)

    def load_annotations_file(self, path: str):
        """Load annotations from a JSON file containing a list of annotation dicts"""
        with open(path, encoding="utf-8") as f:
            self.load_annotations(json.load(f))

    def load_harness_report(self, report: Dict):
        """
        Build trajectories from an IterationTestHarness report
        (the dict returned by generate_test_report()).
        """
        task_id = report["task_id"]
        for key, data in report["propagation_details"].items():
            trajectory = HallucinationTrajectory(
                hallucination_id=f"{task_id}:{key}",
                task_id=task_id,
                instances=[],
                state_transitions=[],
                persistence_duration=0,
                final_state=HallucinationState.PERSIST,
            )
            for inst in data["instances"]:
                instance = self._instance_from_dict({
                    "hallucination_id": key,
                    "task_id": task_id,
                    "iteration": inst["iteration"],
                    "type": data["type"],
                    "description": inst.get("description", ""),
                    "code_snippet": inst.get("code_snippet", ""),
                    "detected_by": inst.get("detected_by", "test_harness"),
                })
                trajectory.add_instance(instance, HallucinationState.PERSIST)

            final_state = HallucinationState(data["final_state"]) \
                if data["final_state"] in STATES else HallucinationState.PERSIST
            if final_state == HallucinationState.RESOLVE:
                # The hallucination disappeared in the iteration after its last appearance
                resolved_at = trajectory.instances[-1].iteration + 1
                trajectory.state_transitions.append((resolved_at, HallucinationState.RESOLVE))
            trajectory.final_state = final_state
            trajectory.persistence_duration = self._duration(trajectory)
            self.add_trajectory(trajectory)

    # ------------------------------------------------------------------
    # Metrics
    # ------------------------------------------------------------------

    def compute_persistence_rate(self, halluc_type: str = None) -> Dict:
        """Compute persistence rate"""
        trajectories = (
            self.hallucinations_by_type.get(halluc_type, []) if halluc_type
            else list(self.trajectories.values())
        )

        if not trajectories:
            return {
                "hallucination_type": halluc_type,
                "persistence_rate": None,
                "total_trajectories": 0,
                "persisted_trajectories": 0,
            }

        persisted = sum(1 for t in trajectories if self._is_persistent(t))
        return {
            "hallucination_type": halluc_type,
            "persistence_rate": persisted / len(trajectories),
            "total_trajectories": len(trajectories),
            "persisted_trajectories": persisted,
        }

    def compute_mutation_rate(self, halluc_type: str = None) -> Dict:
        """Mutation rate = (hallucinations that change form) / (persistent hallucinations)"""
        trajectories = (
            self.hallucinations_by_type.get(halluc_type, []) if halluc_type
            else list(self.trajectories.values())
        )
        persistent = [t for t in trajectories if self._is_persistent(t)]
        mutated = sum(
            1 for t in persistent
            if any(s == HallucinationState.MUTATE for _, s in t.state_transitions)
        )
        return {
            "hallucination_type": halluc_type,
            "mutation_rate": mutated / len(persistent) if persistent else None,
            "persistent_trajectories": len(persistent),
            "mutated_trajectories": mutated,
        }

    def compute_persistence_durations(self, halluc_type: str = None) -> Tuple[List[int], List[str]]:
        """Return (durations, types) for use with StatisticalAnalyzer.persistence_duration_analysis"""
        trajectories = (
            self.hallucinations_by_type.get(halluc_type, []) if halluc_type
            else list(self.trajectories.values())
        )
        durations = [self._duration(t) for t in trajectories]
        types = [self._trajectory_type(t) for t in trajectories]
        return durations, types

    def compute_state_transition_matrix(self) -> pd.DataFrame:
        """Count transitions between consecutive states across all trajectories"""
        matrix = pd.DataFrame(0, index=STATES, columns=STATES)
        for trajectory in self.trajectories.values():
            states = [s.value for _, s in trajectory.state_transitions]
            for current, nxt in zip(states, states[1:]):
                matrix.loc[current, nxt] += 1
        return matrix

    def get_type_counts(self) -> Dict[str, Dict]:
        """{type: {"count": n, "persisting": k}} - the format used by chi_square_test_h2"""
        return {
            h_type: {
                "count": len(trajs),
                "persisting": sum(1 for t in trajs if self._is_persistent(t)),
            }
            for h_type, trajs in self.hallucinations_by_type.items()
        }

    # ------------------------------------------------------------------
    # DataFrames for PropagationVisualizer
    # ------------------------------------------------------------------

    def persistence_by_type_df(self) -> pd.DataFrame:
        rows = [self.compute_persistence_rate(t) for t in self.hallucinations_by_type]
        return pd.DataFrame(rows, columns=[
            "hallucination_type", "persistence_rate",
            "total_trajectories", "persisted_trajectories",
        ])

    def mutation_by_type_df(self) -> pd.DataFrame:
        rows = [self.compute_mutation_rate(t) for t in self.hallucinations_by_type]
        df = pd.DataFrame(rows, columns=[
            "hallucination_type", "mutation_rate",
            "persistent_trajectories", "mutated_trajectories",
        ])
        return df.dropna(subset=["mutation_rate"])

    def persistence_by_severity_df(self) -> pd.DataFrame:
        by_severity = defaultdict(list)
        for trajectory in self.trajectories.values():
            if trajectory.instances:
                by_severity[trajectory.instances[0].severity.value].append(trajectory)

        rows = []
        for severity in [s.value for s in Severity]:
            trajs = by_severity.get(severity)
            if trajs:
                persisted = sum(1 for t in trajs if self._is_persistent(t))
                rows.append({
                    "severity": severity,
                    "persistence_rate": persisted / len(trajs),
                    "count": len(trajs),
                })
        return pd.DataFrame(rows, columns=["severity", "persistence_rate", "count"])

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------

    def get_summary_stats(self) -> Dict:
        """Summary statistics (format used by PropagationVisualizer.create_summary_dashboard)"""
        overall_persistence = self.compute_persistence_rate()["persistence_rate"]
        overall_mutation = self.compute_mutation_rate()["mutation_rate"]
        return {
            "corpus_id": self.corpus_id,
            "total_hallucinations": len(self.trajectories),
            "total_tasks": len(self.task_trajectories),
            "hallucinations_by_type": {
                t: len(trajs) for t, trajs in self.hallucinations_by_type.items()
            },
            "overall_persistence_rate": overall_persistence or 0.0,
            "overall_mutation_rate": overall_mutation or 0.0,
        }

    def export_results(self, path: str) -> str:
        """Save metrics and per-trajectory summaries to JSON"""
        results = {
            "corpus_id": self.corpus_id,
            "generated_at": datetime.now().isoformat(),
            "summary": self.get_summary_stats(),
            "persistence_by_type": {
                t: self.compute_persistence_rate(t) for t in self.hallucinations_by_type
            },
            "mutation_by_type": {
                t: self.compute_mutation_rate(t) for t in self.hallucinations_by_type
            },
            "state_transitions": self.compute_state_transition_matrix().to_dict(),
            "trajectories": [
                self._trajectory_summary(t) for t in self.trajectories.values()
            ],
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        return path

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _instance_from_dict(ann: Dict) -> HallucinationInstance:
        halluc_type = HallucinationType(ann["type"])
        severity = (
            Severity(ann["severity"]) if ann.get("severity")
            else get_hallucination_severity(halluc_type)
        )
        return HallucinationInstance(
            id=ann["hallucination_id"],
            task_id=ann["task_id"],
            iteration=ann["iteration"],
            code_snippet=ann.get("code_snippet", ""),
            hallucination_type=halluc_type,
            severity=severity,
            location=str(ann.get("location", "")),
            description=ann.get("description", ""),
            detected_by=ann.get("detected_by", ""),
        )

    @staticmethod
    def _trajectory_type(trajectory: HallucinationTrajectory) -> Optional[str]:
        if not trajectory.instances:
            return None
        return trajectory.instances[0].hallucination_type.value

    @staticmethod
    def _active_iterations(trajectory: HallucinationTrajectory) -> Set[int]:
        """Iterations in which the hallucination was present (not resolved)"""
        return {
            iteration for iteration, state in trajectory.state_transitions
            if state != HallucinationState.RESOLVE
        }

    def _is_persistent(self, trajectory: HallucinationTrajectory) -> bool:
        """A hallucination persists if it appears in 2+ iterations"""
        return len(self._active_iterations(trajectory)) >= 2

    def _duration(self, trajectory: HallucinationTrajectory) -> int:
        """Number of iterations the hallucination survived beyond its first appearance"""
        active = self._active_iterations(trajectory)
        return max(active) - min(active) if active else 0

    def _trajectory_summary(self, trajectory: HallucinationTrajectory) -> Dict:
        summary = trajectory.get_trajectory_summary()
        summary["state_transitions"] = [
            (iteration, state.value) for iteration, state in trajectory.state_transitions
        ]
        summary["persistent"] = self._is_persistent(trajectory)
        return summary

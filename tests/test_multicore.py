import random
import unittest

from planificador_procesos import Process, simulate
from planificador_procesos.core import SUPPORTED_ALGORITHMS


class MulticoreTests(unittest.TestCase):
    def test_rejects_invalid_configuration_and_fractional_times(self):
        for count in (0, -1, 1.5, True, "2", None):
            with self.subTest(core_count=count), self.assertRaises(ValueError):
                simulate([], "FCFS", core_count=count)
        for quantum in (None, 0, -1, 1.5, True, "2"):
            with self.subTest(quantum=quantum), self.assertRaises(ValueError):
                simulate([], "Round Robin", quantum=quantum, core_count=2)
        for arrival, duration in ((0.5, 2), (0, 1.5), (True, 2), (0, True)):
            with self.subTest(arrival=arrival, duration=duration), self.assertRaises(ValueError):
                Process("P1", arrival, duration)

    def test_empty_workload_has_one_empty_timeline_per_core(self):
        result = simulate([], "FCFS", core_count=3)
        self.assertEqual(result.core_count, 3)
        self.assertEqual(result.core_timeline, ((), (), ()))
        self.assertEqual(result.makespan, 0)
        self.assertEqual(result.average_waiting_time, 0)

    def test_fcfs_reuses_each_core_as_soon_as_it_finishes(self):
        result = simulate(
            [Process("P1", 0, 5), Process("P2", 0, 2), Process("P3", 1, 2)],
            "FCFS", core_count=2,
        )
        self.assertEqual(result.core_timeline, (
            ("P1", "P1", "P1", "P1", "P1"),
            ("P2", "P2", "P3", "P3", None),
        ))
        self.assertEqual([p.completed_time for p in result.processes], [5, 2, 4])
        self.assertEqual([p.waiting_time for p in result.processes], [0, 0, 1])

    def test_idle_cores_accept_later_arrivals_without_interrupting_others(self):
        for algorithm in SUPPORTED_ALGORITHMS:
            with self.subTest(algorithm=algorithm):
                result = simulate(
                    [Process("P1", 2, 5), Process("P2", 4, 1)],
                    algorithm, quantum=10, core_count=3,
                )
                self.assertEqual(result.makespan, 7)
                self.assertEqual([p.completed_time for p in result.processes], [7, 5])
                self.assertEqual([p.waiting_time for p in result.processes], [0, 0])
                self.assertTrue(all(row[:2] == (None, None) for row in result.core_timeline))

    def test_arrival_order_precedes_input_order(self):
        result = simulate(
            [Process("late", 3, 1), Process("early", 2, 2), Process("first", 0, 5)],
            "FCFS",
        )
        self.assertEqual([p.process_id for p in result.processes], ["late", "early", "first"])
        self.assertEqual(result.core_timeline[0], ("first",) * 5 + ("early",) * 2 + ("late",))

    def test_sjf_selects_shortest_ready_jobs_without_preemption(self):
        result = simulate(
            [Process("P1", 0, 5), Process("P2", 0, 3), Process("P3", 0, 2), Process("P4", 1, 1)],
            "SJF", core_count=2,
        )
        self.assertEqual(result.core_timeline, (
            ("P3", "P3", "P4", "P1", "P1", "P1", "P1", "P1"),
            ("P2", "P2", "P2", None, None, None, None, None),
        ))
        self.assertEqual([p.completed_time for p in result.processes], [8, 3, 2, 3])

    def test_srtf_preempts_only_the_longer_job_and_keeps_the_other_on_its_core(self):
        result = simulate(
            [Process("P1", 0, 8), Process("P2", 0, 4), Process("P3", 1, 1)],
            "SRTF", core_count=2,
        )
        self.assertEqual(result.core_timeline[0], ("P2",) * 4 + (None,) * 5)
        self.assertEqual(result.core_timeline[1], ("P1", "P3") + ("P1",) * 7)
        self.assertEqual([p.completed_time for p in result.processes], [9, 4, 2])
        self.assertEqual([p.waiting_time for p in result.processes], [1, 0, 0])

    def test_round_robin_rotates_simultaneous_expirations_in_core_order(self):
        result = simulate(
            [Process("P1", 0, 4), Process("P2", 0, 4), Process("P3", 0, 2)],
            "Round Robin", quantum=2, core_count=2,
        )
        self.assertEqual(result.core_timeline, (
            ("P1", "P1", "P3", "P3", "P2", "P2"),
            ("P2", "P2", "P1", "P1", None, None),
        ))
        self.assertEqual([p.completed_time for p in result.processes], [4, 6, 4])
        self.assertEqual([p.waiting_time for p in result.processes], [0, 2, 2])

    def test_round_robin_new_arrivals_precede_expired_turns(self):
        result = simulate(
            [Process("P1", 0, 4), Process("P2", 0, 4), Process("P3", 2, 1)],
            "Round Robin", quantum=2, core_count=2,
        )
        self.assertEqual(result.core_timeline, (
            ("P1", "P1", "P3", "P2", "P2"),
            ("P2", "P2", "P1", "P1", None),
        ))
        self.assertEqual([p.completed_time for p in result.processes], [4, 5, 3])

    def test_round_robin_quantum_is_independent_for_each_core(self):
        result = simulate(
            [Process("P1", 0, 4), Process("P2", 1, 3), Process("P3", 1, 2)],
            "Round Robin", quantum=2, core_count=2,
        )
        self.assertEqual(result.core_timeline, (
            ("P1", "P1", "P3", "P3", "P2"),
            (None, "P2", "P2", "P1", "P1"),
        ))

    def test_ties_preserve_input_order(self):
        for algorithm in SUPPORTED_ALGORITHMS:
            with self.subTest(algorithm=algorithm):
                result = simulate(
                    [Process("Z", 0, 2), Process("A", 0, 2), Process("B", 0, 2)],
                    algorithm, quantum=2, core_count=2,
                )
                self.assertEqual(result.core_timeline, (("Z", "Z", "B", "B"), ("A", "A", None, None)))

    def test_extra_cores_do_not_speed_up_a_single_process(self):
        for algorithm in SUPPORTED_ALGORITHMS:
            with self.subTest(algorithm=algorithm):
                result = simulate([Process("P1", 0, 5)], algorithm, quantum=2, core_count=8)
                self.assertEqual(result.makespan, 5)
                self.assertEqual(result.core_timeline[0], ("P1",) * 5)
                self.assertTrue(all(row == (None,) * 5 for row in result.core_timeline[1:]))

    def test_generated_workloads_obey_capacity_conservation_and_metrics(self):
        rng = random.Random(20261001)
        for case in range(40):
            processes = [Process(f"P{i}", rng.randrange(9), rng.randrange(1, 8)) for i in range(rng.randrange(1, 9))]
            for algorithm in SUPPORTED_ALGORITHMS:
                for cores in (1, 2, 3, 8):
                    with self.subTest(case=case, algorithm=algorithm, cores=cores):
                        result = simulate(processes, algorithm, quantum=1 + case % 4, core_count=cores)
                        self.assertEqual(len(result.processes), len(processes))
                        self.assertEqual(result.makespan, max(p.completed_time for p in result.processes))
                        self.assertTrue(all(len(row) == result.makespan for row in result.core_timeline))
                        for process, metrics in zip(processes, result.processes):
                            cells = result.timeline[process.process_id]
                            self.assertEqual(cells.count("X"), process.duration_time)
                            self.assertEqual(cells.count("O"), metrics.waiting_time)
                            self.assertEqual(metrics.turnaround_time, metrics.completed_time - process.arrival_time)
                            self.assertEqual(metrics.waiting_time, metrics.turnaround_time - process.duration_time)
                            self.assertGreaterEqual(metrics.waiting_time, 0)
                            self.assertEqual(cells[:process.arrival_time], ("",) * process.arrival_time)
                            self.assertEqual(cells[metrics.completed_time - 1], "X")
                            self.assertTrue(all(cell == "" for cell in cells[metrics.completed_time:]))
                        for time in range(result.makespan):
                            active = [row[time] for row in result.core_timeline if row[time] is not None]
                            self.assertEqual(len(active), len(set(active)))
                            self.assertEqual(set(active), {pid for pid, cells in result.timeline.items() if cells[time] == "X"})
                            eligible = [p for p in result.processes if p.arrival_time <= time < p.completed_time]
                            self.assertEqual(len(active), min(cores, len(eligible)))
                            if algorithm == "SRTF":
                                by_id = {p.process_id: p for p in processes}
                                remaining = lambda p: p.duration_time - result.timeline[p.process_id][:time].count("X")
                                selected = sorted(eligible, key=lambda p: (remaining(p), p.arrival_time, processes.index(by_id[p.process_id])))[:cores]
                                self.assertEqual(set(active), {p.process_id for p in selected})


if __name__ == "__main__":
    unittest.main()

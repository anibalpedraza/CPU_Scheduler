import unittest

from planificador_procesos import Process, simulate


class ProcessValidationTests(unittest.TestCase):
    def test_rejects_invalid_process_values(self) -> None:
        with self.assertRaises(ValueError):
            Process("", 0, 1)
        with self.assertRaises(ValueError):
            Process("P1", -1, 1)
        with self.assertRaises(ValueError):
            Process("P1", 0, 0)

    def test_rejects_duplicate_identifiers(self) -> None:
        processes = [Process("P1", 0, 1), Process("P1", 2, 3)]
        with self.assertRaises(ValueError):
            simulate(processes, "FCFS")

    def test_round_robin_requires_positive_quantum(self) -> None:
        with self.assertRaises(ValueError):
            simulate([Process("P1", 0, 1)], "Round Robin", quantum=0)


class SchedulerTests(unittest.TestCase):
    def test_fcfs_metrics(self) -> None:
        result = simulate(
            [Process("P1", 0, 5), Process("P2", 2, 3)],
            "FCFS",
        )
        p1, p2 = result.processes
        self.assertEqual((p1.completed_time, p1.waiting_time, p1.turnaround_time), (5, 0, 5))
        self.assertEqual((p2.completed_time, p2.waiting_time, p2.turnaround_time), (8, 3, 6))
        self.assertEqual(result.makespan, 8)

    def test_sjf_orders_jobs_by_duration(self) -> None:
        result = simulate(
            [
                Process("P1", 0, 4),
                Process("P2", 0, 2),
                Process("P3", 0, 1),
            ],
            "SJF",
        )
        by_id = {item.process_id: item for item in result.processes}
        self.assertEqual(by_id["P3"].completed_time, 1)
        self.assertEqual(by_id["P2"].completed_time, 3)
        self.assertEqual(by_id["P1"].completed_time, 7)

    def test_srtf_preempts_for_shorter_arrivals(self) -> None:
        result = simulate(
            [
                Process("P1", 0, 6),
                Process("P2", 1, 3),
                Process("P3", 2, 1),
            ],
            "SRTF",
        )
        by_id = {item.process_id: item for item in result.processes}
        self.assertEqual(by_id["P3"].completed_time, 3)
        self.assertEqual(by_id["P2"].completed_time, 5)
        self.assertEqual(by_id["P1"].completed_time, 10)
        self.assertEqual(result.timeline["P3"][2], "X")

    def test_round_robin_rotates_after_quantum(self) -> None:
        result = simulate(
            [Process("P1", 0, 4), Process("P2", 0, 2)],
            "Round Robin",
            quantum=2,
        )
        by_id = {item.process_id: item for item in result.processes}
        self.assertEqual(by_id["P2"].completed_time, 4)
        self.assertEqual(by_id["P1"].completed_time, 6)
        self.assertEqual(result.timeline["P1"], ("X", "X", "O", "O", "X", "X"))
        self.assertEqual(result.timeline["P2"], ("O", "O", "X", "X", "", ""))

    def test_empty_workload_has_zero_averages(self) -> None:
        result = simulate([], "FCFS")
        self.assertEqual(result.average_waiting_time, 0.0)
        self.assertEqual(result.average_turnaround_time, 0.0)


if __name__ == "__main__":
    unittest.main()

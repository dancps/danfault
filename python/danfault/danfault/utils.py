import logging
from time import (
    monotonic,
    perf_counter,
    perf_counter_ns,
    process_time,
    thread_time,
    time,
)
from typing import List

import numpy as np
import pandas as pd
from danfault.logs import Loggir
from termcolor import colored


class Performance:
    def __init__(
        self, method, args, iterations: int = 1000, perf_methods: List[str] = None, debug=False
    ) -> None:
        self.logger = Loggir()
        self.method = method
        self.args = args

        self.iterations = iterations
        self.perf_methods = perf_methods
        self.allowed_perf_methods = {
            "perf_counter": self._run_perf_counter,
            "perf_counter_ns": self._run_perf_counter_ns,
            "time": self._run_time,
            "monotonic": self._run_monotonic,
            "process_time": self._run_process_time,
            "thread_time": self._run_thread_time,
        }
        self.debug = debug
        if debug:
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger.setLevel(logging.INFO)
        self.results_dict = {}
        self._run_methods()
        self.results_df = None
        self.results_summary_ms = None
        self._create_dataframe()
        self._create_dataframe_summary()

    def _run_methods(self):
        self.logger.info("Running")
        if self.perf_methods is None:
            self.perf_methods = list(self.allowed_perf_methods.keys())
        else:
            # Check if the methods are in allowd meths
            for i in self.perf_methods:
                if not i in self.allowed_perf_methods:
                    raise ValueError(
                        f"The method {i} is not part of the allowed methods. Choose from the list below:\n {list(self.allowed_perf_methods.keys())}"
                    )
        for i in self.perf_methods:
            self.logger.debug(f"Calling {colored(i, attrs=['bold'])}")
            self.allowed_perf_methods[i]()

    def _run_generic_performance(self, method, function, args):
        start = method()
        function(*args)
        end = method()
        return end - start

    def _run_perf_counter(self):
        self.logger.debug(f"Running {colored('_run_perf_counter', attrs=['bold'])}")

        res_list = [
            self._run_generic_performance(perf_counter, self.method, self.args)
            for _ in range(0, self.iterations)
        ]
        self.results_dict["perf_counter"] = np.array(res_list)

    def _run_perf_counter_ns(self):
        self.logger.debug(f"Running {colored('_run_perf_counter_ns', attrs=['bold'])}")
        res_list = [
            self._run_generic_performance(perf_counter_ns, self.method, self.args)
            for _ in range(0, self.iterations)
        ]

        self.results_dict["perf_counter_ns"] = np.array(res_list)

    def _run_time(self):
        self.logger.debug(f"Running {colored('_run_time', attrs=['bold'])}")
        # self.logger.warning(f"Function _run_time was not implemented yet.")
        res_list = [
            self._run_generic_performance(time, self.method, self.args)
            for _ in range(0, self.iterations)
        ]
        self.results_dict["time"] = np.array(res_list)

    def _run_monotonic(self):
        self.logger.debug(f"Running {colored('_run_monotonic', attrs=['bold'])}")
        # self.logger.warning(f"Function _run_monotonic was not implemented yet.")
        res_list = [
            self._run_generic_performance(monotonic, self.method, self.args)
            for _ in range(0, self.iterations)
        ]
        self.results_dict["monotonic"] = np.array(res_list)

    def _run_process_time(self):
        self.logger.debug(f"Running {colored('_run_process_time', attrs=['bold'])}")
        # self.logger.warning(f"Function _run_process_time was not implemented yet.")
        res_list = [
            self._run_generic_performance(process_time, self.method, self.args)
            for _ in range(0, self.iterations)
        ]
        self.results_dict["process_time"] = np.array(res_list)

    def _run_thread_time(self):
        self.logger.debug(f"Running {colored('_run_thread_time', attrs=['bold'])}")
        # self.logger.warning(f"Function _run_thread_time was not implemented yet.")
        res_list = [
            self._run_generic_performance(thread_time, self.method, self.args)
            for _ in range(0, self.iterations)
        ]
        self.results_dict["thread_time"] = np.array(res_list)

    def _create_dataframe(self):
        self.results_df = pd.DataFrame(self.results_dict)

    def _create_dataframe_summary(self):
        results_df = self.results_df_in_ms()
        self.results_summary_ms = results_df.agg(["count", "min", "max", "median", "mean", "std"]).T

    def results_df_in_ms(self):
        results_df = self.results_df.copy()
        for col in self.results_df.columns:
            if col == "perf_counter_ns":
                results_df[col] = results_df[col] / 1000000
            else:

                results_df[col] = results_df[col] * 1000
        return results_df

    def get_dataframe(self):
        return self.results_df

    def get_dataframe_summary(self):
        return self.results_summary_ms

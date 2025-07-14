from threading import Thread
from typing import Dict

running_strategies: Dict[str, bool] = {}
active_threads: Dict[str, Thread] = {}

def start_strategy_flag(strategy_id: str):
    running_strategies[strategy_id] = True

def stop_strategy_flag(strategy_id: str):
    running_strategies[strategy_id] = False

def is_running(strategy_id: str) -> bool:
    return running_strategies.get(strategy_id, False)

def register_thread(strategy_id: str, thread: Thread):
    active_threads[strategy_id] = thread

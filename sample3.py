import threading
import time
import queue
import random
from enum import Enum

class Signal(Enum):
    BUY = 1
    SELL = 2
    WAITING_TO_BUY = 3
    WAITING_TO_SELL = 4

def process_signals(signal_queue):
    while True:
        if not signal_queue.empty():
            signal, price = signal_queue.get()
            if signal == Signal.BUY:
                print("Received BUY signal at price:", price)
                # Place buy order or trigger appropriate action
            elif signal == Signal.SELL:
                print("Received SELL signal at price:", price)
                # Place sell order or trigger appropriate action
            elif signal == Signal.WAITING_TO_BUY:
                print("Waiting to buy at price:", price)
            elif signal == Signal.WAITING_TO_SELL:
                print("Waiting to sell at price:", price)
        time.sleep(1)  # Adjust sleep time as needed

def fetch_candle_data(signal_queue):
    while True:
        # Simulate fetching candle data and calculating the price
        price = random.uniform(100, 200)  # Random price between 100 and 200
        # Put the price into the queue along with the corresponding signal
        signal_queue.put((Signal.BUY, price))
        time.sleep(20)  # Simulate fetching candle data every 20 seconds

def compare_with_ltp(signal_queue):
    while True:
        # Simulate fetching LTP data
        ltp = random.uniform(150, 250)  # Random LTP between 150 and 250
        # Retrieve the price calculated from candle data
        price = signal_queue.get()[1]  # Get the price from the queue
        # Compare with LTP and trigger buy/sell signals accordingly
        if price > ltp:
            signal_queue.put((Signal.BUY, ltp))
        else:
            signal_queue.put((Signal.SELL, ltp))
        time.sleep(1)  # Simulate comparing with LTP every second

def main():
    # Create a queue to pass signals and prices between threads
    signal_queue = queue.Queue()

    # Start threads for fetching candle data, comparing with LTP, and processing signals
    threading.Thread(target=fetch_candle_data, args=(signal_queue,), daemon=True).start()
    threading.Thread(target=compare_with_ltp, args=(signal_queue,), daemon=True).start()
    threading.Thread(target=process_signals, args=(signal_queue,), daemon=True).start()

    while True:
        time.sleep(1)  # Keep the main thread alive

if __name__ == "__main__":
    main()

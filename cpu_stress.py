#!/usr/bin/env python3
"""
CPU Stress Test Script for GitHub Actions Runners
=================================================

This script performs controlled CPU stress testing by utilizing multiple cores
with various computational workloads for a specified duration.

Usage:
    python cpu_stress.py [cpu_percentage] [duration_seconds] [job_id]

Arguments:
    cpu_percentage: Percentage of CPU cores to utilize (10-100, default: 80)
    duration_seconds: How long to run the stress test in seconds (default: 60)
    job_id: Optional job identifier for logging (default: "unknown")

Features:
    - Cross-platform support (Linux, macOS, Windows)
    - Multi-core CPU stress testing
    - Various computational workloads (math, prime finding, sorting, etc.)
    - Real-time CPU usage monitoring
    - Temperature monitoring (where available)
    - Proper cleanup and resource management
    - System information reporting
"""

import sys
import time
import math
import random
import platform
import psutil
import threading
import multiprocessing
from datetime import datetime
from typing import List, Optional, Callable
import hashlib
import json


class CPUStresser:
    """
    A class to perform controlled CPU stress testing.
    """
    
    def __init__(self, cpu_percentage: int = 80, duration_seconds: int = 60, job_id: str = "unknown"):
        """
        Initialize the CPU stresser.
        
        Args:
            cpu_percentage: Percentage of CPU cores to utilize (10-100)
            duration_seconds: Duration to run stress test in seconds
            job_id: Job identifier for logging
        """
        self.cpu_percentage = max(10, min(100, cpu_percentage))
        self.duration_seconds = duration_seconds
        self.job_id = job_id
        self.running = True
        self.start_time = None
        
        # CPU information
        self.total_cores = psutil.cpu_count(logical=True)
        self.physical_cores = psutil.cpu_count(logical=False)
        self.target_cores = max(1, int(self.total_cores * self.cpu_percentage / 100))
        
        # Worker processes and monitoring
        self.worker_processes: List[multiprocessing.Process] = []
        self.stop_event = multiprocessing.Event()
        
        # Get system info
        self.system_info = self._get_system_info()
        
    def _get_system_info(self) -> dict:
        """Get comprehensive system information."""
        try:
            memory = psutil.virtual_memory()
            cpu_freq = psutil.cpu_freq()
            
            return {
                'platform': platform.system(),
                'platform_release': platform.release(),
                'platform_version': platform.version(),
                'architecture': platform.machine(),
                'processor': platform.processor(),
                'total_cores': self.total_cores,
                'physical_cores': self.physical_cores,
                'cpu_freq_current': cpu_freq.current if cpu_freq else 'unknown',
                'cpu_freq_max': cpu_freq.max if cpu_freq else 'unknown',
                'total_memory_gb': round(memory.total / (1024**3), 2),
                'python_version': platform.python_version(),
            }
        except Exception as e:
            print(f"Warning: Could not get full system info: {e}")
            return {
                'platform': platform.system(),
                'total_cores': self.total_cores,
                'physical_cores': self.physical_cores,
            }
    
    def print_banner(self):
        """Print the initial banner with test information."""
        print("=" * 60)
        print("🔥 CPU STRESS TEST")
        print("=" * 60)
        print(f"📊 Job ID: {self.job_id}")
        print(f"🖥️  Platform: {self.system_info['platform']} {self.system_info.get('platform_release', '')}")
        print(f"🏗️  Architecture: {self.system_info['architecture']}")
        print(f"⚙️  Processor: {self.system_info.get('processor', 'Unknown')}")
        print(f"🔢 Total CPU Cores: {self.total_cores} (Physical: {self.physical_cores})")
        print(f"🎯 Target Cores: {self.target_cores} ({self.cpu_percentage}%)")
        print(f"⚡ CPU Frequency: {self.system_info.get('cpu_freq_current', 'unknown')} MHz")
        print(f"⏱️  Duration: {self.duration_seconds} seconds")
        print(f"📅 Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        print()

    @staticmethod
    def cpu_intensive_work(worker_id: int, stop_event: multiprocessing.Event, duration: int):
        """
        CPU-intensive work function that runs in separate processes.
        
        Args:
            worker_id: Unique identifier for this worker
            stop_event: Event to signal when to stop
            duration: Maximum duration to run
        """
        start_time = time.time()
        iteration = 0
        
        print(f"🔥 Worker {worker_id} started on PID {multiprocessing.current_process().pid}")
        
        # Different workload types to vary CPU usage patterns
        workload_functions = [
            CPUStresser._mathematical_operations,
            CPUStresser._prime_number_generation,
            CPUStresser._sorting_operations,
            CPUStresser._hash_calculations,
            CPUStresser._matrix_operations,
        ]
        
        try:
            while not stop_event.is_set() and (time.time() - start_time) < duration:
                iteration += 1
                
                # Rotate through different workload types
                workload_func = workload_functions[iteration % len(workload_functions)]
                workload_func(worker_id, iteration)
                
                # Brief yield to allow monitoring
                if iteration % 1000 == 0:
                    time.sleep(0.001)  # 1ms yield every 1000 iterations
                    
        except KeyboardInterrupt:
            pass
        except Exception as e:
            print(f"⚠️  Worker {worker_id} error: {e}")
        finally:
            elapsed = time.time() - start_time
            print(f"✅ Worker {worker_id} completed after {elapsed:.2f}s ({iteration} iterations)")

    @staticmethod
    def _mathematical_operations(worker_id: int, iteration: int):
        """Perform various mathematical operations."""
        base = iteration % 10000 + 1
        
        # Trigonometric calculations
        result = math.sin(base) * math.cos(base)
        result += math.sqrt(abs(result * base))
        result += math.log(base + 1)
        
        # Power operations
        result += pow(base % 100, 3)
        result += base ** 0.5
        
        # Factorial for smaller numbers
        if base % 1000 < 10:
            result += math.factorial(base % 1000)
        
        return result

    @staticmethod
    def _prime_number_generation(worker_id: int, iteration: int):
        """Generate and check prime numbers."""
        start = (iteration % 10000) + 2
        end = start + 100
        
        primes = []
        for num in range(start, end):
            if num > 1:
                for i in range(2, int(num ** 0.5) + 1):
                    if num % i == 0:
                        break
                else:
                    primes.append(num)
        
        return len(primes)

    @staticmethod
    def _sorting_operations(worker_id: int, iteration: int):
        """Perform various sorting operations on random data."""
        size = 1000 + (iteration % 500)
        data = [random.randint(1, 10000) for _ in range(size)]
        
        # Different sorting algorithms
        if iteration % 4 == 0:
            data.sort()  # Timsort
        elif iteration % 4 == 1:
            data.sort(reverse=True)
        elif iteration % 4 == 2:
            # Bubble sort for smaller datasets
            if len(data) < 100:
                for i in range(len(data)):
                    for j in range(0, len(data) - i - 1):
                        if data[j] > data[j + 1]:
                            data[j], data[j + 1] = data[j + 1], data[j]
        else:
            # Selection sort for smaller datasets
            if len(data) < 100:
                for i in range(len(data)):
                    min_idx = i
                    for j in range(i + 1, len(data)):
                        if data[j] < data[min_idx]:
                            min_idx = j
                    data[i], data[min_idx] = data[min_idx], data[i]
        
        return len(data)

    @staticmethod
    def _hash_calculations(worker_id: int, iteration: int):
        """Perform hash calculations on varying data."""
        data_size = 1000 + (iteration % 1000)
        data = bytes(random.randint(0, 255) for _ in range(data_size))
        
        # Different hash algorithms
        if iteration % 3 == 0:
            result = hashlib.sha256(data).hexdigest()
        elif iteration % 3 == 1:
            result = hashlib.md5(data).hexdigest()
        else:
            result = hashlib.sha1(data).hexdigest()
        
        return len(result)

    @staticmethod
    def _matrix_operations(worker_id: int, iteration: int):
        """Perform matrix operations."""
        size = 20 + (iteration % 10)  # Small matrices to avoid memory issues
        
        # Create random matrices
        matrix_a = [[random.random() for _ in range(size)] for _ in range(size)]
        matrix_b = [[random.random() for _ in range(size)] for _ in range(size)]
        
        # Matrix multiplication
        result = [[0 for _ in range(size)] for _ in range(size)]
        for i in range(size):
            for j in range(size):
                for k in range(size):
                    result[i][j] += matrix_a[i][k] * matrix_b[k][j]
        
        return result[0][0]  # Return just one element

    def start_cpu_workers(self):
        """Start CPU worker processes."""
        print("🚀 STARTING CPU WORKERS")
        print("=" * 25)
        print(f"Launching {self.target_cores} worker processes...")
        
        self.stop_event.clear()
        
        for i in range(self.target_cores):
            worker = multiprocessing.Process(
                target=self.cpu_intensive_work,
                args=(i + 1, self.stop_event, self.duration_seconds),
                name=f"CPUWorker-{i+1}"
            )
            worker.start()
            self.worker_processes.append(worker)
            print(f"   ✅ Started worker {i+1} (PID: {worker.pid})")
            
            # Small delay between worker starts
            time.sleep(0.1)
        
        print(f"✅ All {len(self.worker_processes)} workers started")
        print()

    def monitor_cpu_usage(self):
        """Monitor CPU usage during the stress test."""
        print("📊 CPU MONITORING STARTED")
        print("=" * 25)
        
        monitoring_interval = 2.0  # Monitor every 2 seconds
        last_report = time.time()
        
        # Get initial CPU readings
        psutil.cpu_percent(interval=None)  # Initialize
        
        while self.running and any(worker.is_alive() for worker in self.worker_processes):
            current_time = time.time()
            
            if current_time - last_report >= monitoring_interval:
                elapsed = current_time - self.start_time if self.start_time else 0
                remaining = max(0, self.duration_seconds - elapsed)
                
                try:
                    # Get CPU usage
                    cpu_percent = psutil.cpu_percent(interval=1.0)
                    cpu_per_core = psutil.cpu_percent(interval=None, percpu=True)
                    
                    # Get system load
                    try:
                        load_avg = psutil.getloadavg()
                        load_str = f"{load_avg[0]:.2f}, {load_avg[1]:.2f}, {load_avg[2]:.2f}"
                    except (AttributeError, OSError):
                        load_str = "N/A"
                    
                    # Get CPU frequency
                    try:
                        cpu_freq = psutil.cpu_freq()
                        freq_str = f"{cpu_freq.current:.0f} MHz" if cpu_freq else "N/A"
                    except:
                        freq_str = "N/A"
                    
                    # Get temperature (if available)
                    temp_str = "N/A"
                    try:
                        temps = psutil.sensors_temperatures()
                        if temps:
                            # Try to get CPU temperature
                            for name, entries in temps.items():
                                if 'cpu' in name.lower() or 'core' in name.lower():
                                    if entries:
                                        temp_str = f"{entries[0].current:.1f}°C"
                                        break
                    except:
                        pass
                    
                    # Active workers count
                    active_workers = sum(1 for worker in self.worker_processes if worker.is_alive())
                    
                    print(f"⏱️  [{elapsed:.1f}s] CPU: {cpu_percent:.1f}% | "
                          f"Workers: {active_workers}/{self.target_cores} | "
                          f"Load: [{load_str}] | "
                          f"Freq: {freq_str} | "
                          f"Temp: {temp_str} | "
                          f"Remaining: {remaining:.1f}s")
                    
                    # Show per-core usage every 10 seconds
                    if int(elapsed) % 10 == 0 and len(cpu_per_core) <= 16:  # Don't spam for too many cores
                        core_usage = " | ".join([f"C{i}:{usage:.0f}%" for i, usage in enumerate(cpu_per_core)])
                        print(f"     Per-core: {core_usage}")
                    
                except Exception as e:
                    print(f"⚠️  Monitoring error: {e}")
                
                last_report = current_time
            
            time.sleep(0.5)  # Check every 500ms

    def wait_for_completion(self):
        """Wait for all workers to complete and clean up."""
        print("⏳ WAITING FOR COMPLETION")
        print("=" * 25)
        
        try:
            # Wait for the specified duration
            time.sleep(self.duration_seconds)
            
            # Signal workers to stop
            print("🛑 Signaling workers to stop...")
            self.stop_event.set()
            
            # Wait for workers to finish gracefully
            for i, worker in enumerate(self.worker_processes):
                worker.join(timeout=5.0)  # 5 second timeout per worker
                if worker.is_alive():
                    print(f"⚠️  Worker {i+1} didn't stop gracefully, terminating...")
                    worker.terminate()
                    worker.join(timeout=2.0)
                    if worker.is_alive():
                        print(f"❌ Force killing worker {i+1}")
                        worker.kill()
                        worker.join()
            
            print("✅ All workers stopped")
            
        except KeyboardInterrupt:
            print("\n⚠️  Test interrupted by user")
            self.stop_event.set()
            
            # Force terminate all workers
            for worker in self.worker_processes:
                if worker.is_alive():
                    worker.terminate()
                    worker.join(timeout=1.0)
                    if worker.is_alive():
                        worker.kill()
                        worker.join()

    def print_summary(self):
        """Print final test summary."""
        print("\n" + "=" * 60)
        print("📋 CPU STRESS TEST SUMMARY")
        print("=" * 60)
        
        if self.start_time:
            total_duration = time.time() - self.start_time
            print(f"⏱️  Total Test Duration: {total_duration:.2f} seconds")
        
        try:
            # Final CPU measurements
            final_cpu = psutil.cpu_percent(interval=1.0)
            cpu_count = psutil.cpu_count(logical=True)
            
            print(f"⚙️  Final CPU Usage: {final_cpu:.1f}%")
            print(f"🔢 CPU Cores Used: {self.target_cores}/{cpu_count}")
            print(f"📊 Target CPU Utilization: {self.cpu_percentage}%")
            
            # Load average
            try:
                load_avg = psutil.getloadavg()
                print(f"📈 System Load: {load_avg[0]:.2f} (1m), {load_avg[1]:.2f} (5m), {load_avg[2]:.2f} (15m)")
            except:
                print("📈 System Load: N/A")
                
        except Exception as e:
            print(f"📊 Final CPU Usage: Unable to determine ({e})")
        
        print(f"🎯 Target Cores: {self.target_cores}")
        print(f"📊 Job ID: {self.job_id}")
        print(f"🖥️  Platform: {self.system_info['platform']}")
        print(f"📅 Completion Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("✅ CPU stress test completed successfully!")
        print("=" * 60)

    def run(self):
        """Execute the complete CPU stress test."""
        try:
            self.print_banner()
            
            # Start timing
            self.start_time = time.time()
            
            # Start CPU workers
            self.start_cpu_workers()
            
            # Start monitoring in a separate thread
            monitor_thread = threading.Thread(target=self.monitor_cpu_usage, daemon=True)
            monitor_thread.start()
            
            # Wait for completion
            self.wait_for_completion()
            
        except Exception as e:
            print(f"❌ Unexpected error during test: {e}")
        finally:
            # Stop monitoring
            self.running = False
            
            # Clean up any remaining processes
            for worker in self.worker_processes:
                if worker.is_alive():
                    worker.terminate()
                    worker.join(timeout=1.0)
            
            # Print summary
            self.print_summary()


def main():
    """
    Main function to parse arguments and run the CPU stress test.
    """
    # Parse command line arguments
    cpu_percentage = 80     # Default
    duration_seconds = 60   # Default
    job_id = "unknown"      # Default
    
    if len(sys.argv) > 1:
        try:
            cpu_percentage = int(sys.argv[1])
        except ValueError:
            print(f"Warning: Invalid CPU percentage '{sys.argv[1]}', using default 80%")
    
    if len(sys.argv) > 2:
        try:
            duration_seconds = int(sys.argv[2])
        except ValueError:
            print(f"Warning: Invalid duration '{sys.argv[2]}', using default 60 seconds")
    
    if len(sys.argv) > 3:
        job_id = sys.argv[3]
    
    # Validate inputs
    if cpu_percentage < 10 or cpu_percentage > 100:
        print(f"Warning: CPU percentage {cpu_percentage}% is outside range (10-100%), clamping...")
        cpu_percentage = max(10, min(100, cpu_percentage))
    
    if duration_seconds < 1:
        print(f"Warning: Duration {duration_seconds} is too short, using minimum 1 second")
        duration_seconds = 1
    
    # Create and run the stress tester
    stresser = CPUStresser(cpu_percentage, duration_seconds, job_id)
    stresser.run()


if __name__ == "__main__":
    main()

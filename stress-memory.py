#!/usr/bin/env python3
"""
Memory Stress Test Script for GitHub Actions Runners
===================================================

This script performs controlled memory stress testing by allocating and holding
a specified percentage of available system memory for a given duration.

Usage:
    python memory_stress.py [memory_percentage] [duration_seconds] [job_id]

Arguments:
    memory_percentage: Percentage of available memory to consume (10-90, default: 70)
    duration_seconds: How long to hold the memory in seconds (default: 60)
    job_id: Optional job identifier for logging (default: "unknown")

Features:
    - Cross-platform support (Linux, macOS, Windows)
    - Safe memory allocation with error handling
    - Active memory usage to prevent optimization
    - Real-time monitoring and logging
    - Proper cleanup and garbage collection
    - System information reporting
"""

import sys
import time
import gc
import random
import platform
import psutil
import threading
from datetime import datetime
from typing import List, Optional


class MemoryStresser:
    """
    A class to perform controlled memory stress testing.
    """
    
    def __init__(self, memory_percentage: int = 70, duration_seconds: int = 60, job_id: str = "unknown"):
        """
        Initialize the memory stresser.
        
        Args:
            memory_percentage: Percentage of available memory to consume (10-90)
            duration_seconds: Duration to hold memory in seconds
            job_id: Job identifier for logging
        """
        self.memory_percentage = max(10, min(90, memory_percentage))  # Clamp between 10-90%
        self.duration_seconds = duration_seconds
        self.job_id = job_id
        self.memory_chunks: List[bytearray] = []
        self.running = True
        self.chunk_size = 10 * 1024 * 1024  # 10MB chunks
        self.start_time = None
        
        # Get system info
        self.system_info = self._get_system_info()
        
    def _get_system_info(self) -> dict:
        """Get comprehensive system information."""
        try:
            memory = psutil.virtual_memory()
            return {
                'platform': platform.system(),
                'platform_release': platform.release(),
                'platform_version': platform.version(),
                'architecture': platform.machine(),
                'processor': platform.processor(),
                'total_memory_gb': round(memory.total / (1024**3), 2),
                'available_memory_gb': round(memory.available / (1024**3), 2),
                'memory_percent_used': memory.percent,
                'cpu_count': psutil.cpu_count(),
                'cpu_count_logical': psutil.cpu_count(logical=True),
            }
        except Exception as e:
            print(f"Warning: Could not get full system info: {e}")
            return {
                'platform': platform.system(),
                'total_memory_gb': 'unknown',
                'available_memory_gb': 'unknown',
                'cpu_count': 'unknown'
            }
    
    def print_banner(self):
        """Print the initial banner with test information."""
        print("=" * 60)
        print("🧠 MEMORY STRESS TEST")
        print("=" * 60)
        print(f"📊 Job ID: {self.job_id}")
        print(f"🖥️  Platform: {self.system_info['platform']} {self.system_info.get('platform_release', '')}")
        print(f"🏗️  Architecture: {self.system_info['architecture']}")
        print(f"💾 Total Memory: {self.system_info['total_memory_gb']} GB")
        print(f"📈 Available Memory: {self.system_info['available_memory_gb']} GB")
        print(f"🎯 Target Usage: {self.memory_percentage}%")
        print(f"⏱️  Duration: {self.duration_seconds} seconds")
        print(f"📅 Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        print()
    
    def calculate_target_memory(self) -> tuple:
        """
        Calculate target memory allocation based on available memory.
        
        Returns:
            tuple: (target_bytes, target_mb, chunks_needed)
        """
        try:
            memory = psutil.virtual_memory()
            available_bytes = memory.available
            target_bytes = int(available_bytes * self.memory_percentage / 100)
            target_mb = target_bytes // (1024 * 1024)
            chunks_needed = target_mb // 10  # 10MB per chunk
            
            print(f"💾 MEMORY CALCULATION")
            print(f"Available Memory: {available_bytes // (1024*1024)} MB")
            print(f"Target Allocation: {target_mb} MB ({self.memory_percentage}%)")
            print(f"Chunks to Allocate: {chunks_needed} (10MB each)")
            print()
            
            return target_bytes, target_mb, chunks_needed
            
        except Exception as e:
            print(f"❌ Error calculating memory: {e}")
            # Fallback values
            fallback_mb = 1000  # 1GB fallback
            return fallback_mb * 1024 * 1024, fallback_mb, fallback_mb // 10
    
    def allocate_memory(self, chunks_needed: int) -> bool:
        """
        Allocate memory in chunks.
        
        Args:
            chunks_needed: Number of 10MB chunks to allocate
            
        Returns:
            bool: True if allocation successful, False otherwise
        """
        print("🚀 MEMORY ALLOCATION PHASE")
        print("=" * 30)
        
        allocated_chunks = 0
        
        try:
            for i in range(chunks_needed):
                if not self.running:
                    break
                
                # Create chunk with random data to prevent optimization
                chunk = bytearray(self.chunk_size)
                
                # Fill chunk with random data in sections to avoid memory optimization
                random_seed = random.randint(0, 2**32 - 1)
                for j in range(0, self.chunk_size, 4096):  # 4KB sections
                    end_pos = min(j + 4, self.chunk_size)
                    chunk[j:end_pos] = ((random_seed + j) % (2**32)).to_bytes(4, 'big')
                
                self.memory_chunks.append(chunk)
                allocated_chunks += 1
                
                # Progress reporting
                if (i + 1) % 10 == 0 or i == chunks_needed - 1:
                    allocated_mb = allocated_chunks * 10
                    progress = (allocated_chunks / chunks_needed) * 100
                    print(f"📊 Progress: {allocated_mb} MB allocated ({progress:.1f}%)")
                    
                    # Memory status update
                    if (i + 1) % 50 == 0:
                        try:
                            current_memory = psutil.virtual_memory()
                            print(f"   Current system memory usage: {current_memory.percent:.1f}%")
                        except:
                            pass
                            
        except MemoryError:
            print(f"⚠️  Memory allocation limit reached at {allocated_chunks * 10} MB")
        except Exception as e:
            print(f"❌ Allocation error: {e}")
            
        final_allocated_mb = len(self.memory_chunks) * 10
        print(f"✅ Allocation complete: {final_allocated_mb} MB in {len(self.memory_chunks)} chunks")
        print()
        
        return len(self.memory_chunks) > 0
    
    def stress_memory_worker(self):
        """Worker thread to actively use allocated memory."""
        iteration = 0
        while self.running and self.memory_chunks:
            iteration += 1
            
            try:
                # Randomly select a chunk and modify it
                if self.memory_chunks:
                    chunk_index = random.randint(0, len(self.memory_chunks) - 1)
                    chunk = self.memory_chunks[chunk_index]
                    
                    # Write pattern to random locations in the chunk
                    for _ in range(10):  # 10 random writes per iteration
                        pos = random.randint(0, len(chunk) - 8)
                        value = ((iteration + pos) % 256).to_bytes(1, 'big') * 8
                        chunk[pos:pos+8] = value
                
                # Small delay to prevent 100% CPU usage
                time.sleep(0.001)
                
            except Exception as e:
                if self.running:  # Only log if we're supposed to be running
                    print(f"⚠️  Memory worker error: {e}")
                break
    
    def hold_memory(self):
        """
        Hold the allocated memory for the specified duration while actively using it.
        """
        if not self.memory_chunks:
            print("❌ No memory allocated to hold!")
            return
            
        print("🔥 MEMORY STRESS PHASE")
        print("=" * 25)
        print(f"Holding {len(self.memory_chunks) * 10} MB for {self.duration_seconds} seconds...")
        print("Starting active memory usage...")
        print()
        
        # Start worker thread for active memory usage
        worker_thread = threading.Thread(target=self.stress_memory_worker, daemon=True)
        worker_thread.start()
        
        self.start_time = time.time()
        last_report_time = self.start_time
        iteration = 0
        
        while time.time() - self.start_time < self.duration_seconds and self.running:
            iteration += 1
            current_time = time.time()
            elapsed = current_time - self.start_time
            
            # Report progress every 5 seconds
            if current_time - last_report_time >= 5.0:
                remaining = self.duration_seconds - elapsed
                progress = (elapsed / self.duration_seconds) * 100
                
                try:
                    # Get current memory stats
                    memory = psutil.virtual_memory()
                    memory_used_gb = (memory.total - memory.available) / (1024**3)
                    
                    print(f"⏱️  [{elapsed:.1f}s] Progress: {progress:.1f}% | "
                          f"Memory Used: {memory_used_gb:.2f} GB ({memory.percent:.1f}%) | "
                          f"Remaining: {remaining:.1f}s")
                except:
                    print(f"⏱️  [{elapsed:.1f}s] Progress: {progress:.1f}% | Remaining: {remaining:.1f}s")
                
                last_report_time = current_time
            
            time.sleep(0.1)  # Check every 100ms
        
        # Stop the worker thread
        self.running = False
        worker_thread.join(timeout=1.0)
        
        total_duration = time.time() - self.start_time
        print(f"\n✅ Memory stress phase completed in {total_duration:.2f} seconds")
        print()
    
    def cleanup(self):
        """Clean up allocated memory and run garbage collection."""
        print("🧹 CLEANUP PHASE")
        print("=" * 15)
        
        if self.memory_chunks:
            chunks_to_clean = len(self.memory_chunks)
            memory_to_free = chunks_to_clean * 10
            print(f"Releasing {memory_to_free} MB ({chunks_to_clean} chunks)...")
            
            # Clear the memory chunks
            self.memory_chunks.clear()
            
            # Force garbage collection
            print("Running garbage collection...")
            for _ in range(3):  # Multiple GC passes
                gc.collect()
            
            print("✅ Memory cleanup completed!")
        else:
            print("ℹ️  No memory to clean up")
        
        print()
    
    def print_summary(self):
        """Print final test summary."""
        print("=" * 60)
        print("📋 TEST SUMMARY")
        print("=" * 60)
        
        if self.start_time:
            total_duration = time.time() - self.start_time
            print(f"⏱️  Total Test Duration: {total_duration:.2f} seconds")
        
        try:
            final_memory = psutil.virtual_memory()
            print(f"💾 Final Memory Usage: {final_memory.percent:.1f}%")
            print(f"💾 Available Memory: {final_memory.available / (1024**3):.2f} GB")
        except:
            print("💾 Final Memory Usage: Unable to determine")
        
        print(f"🎯 Target Memory Percentage: {self.memory_percentage}%")
        print(f"📊 Job ID: {self.job_id}")
        print(f"🖥️  Platform: {self.system_info['platform']}")
        print(f"📅 Completion Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("✅ Memory stress test completed successfully!")
        print("=" * 60)
    
    def run(self):
        """
        Execute the complete memory stress test.
        """
        try:
            self.print_banner()
            
            # Calculate memory requirements
            target_bytes, target_mb, chunks_needed = self.calculate_target_memory()
            
            # Allocate memory
            if chunks_needed > 0:
                success = self.allocate_memory(chunks_needed)
                if success:
                    # Hold and stress memory
                    self.hold_memory()
                else:
                    print("❌ Memory allocation failed!")
            else:
                print("❌ No memory chunks to allocate!")
            
        except KeyboardInterrupt:
            print("\n⚠️  Test interrupted by user")
            self.running = False
        except Exception as e:
            print(f"❌ Unexpected error during test: {e}")
        finally:
            # Always clean up
            self.cleanup()
            self.print_summary()


def main():
    """
    Main function to parse arguments and run the memory stress test.
    """
    # Parse command line arguments
    memory_percentage = 70  # Default
    duration_seconds = 60   # Default
    job_id = "unknown"      # Default
    
    if len(sys.argv) > 1:
        try:
            memory_percentage = int(sys.argv[1])
        except ValueError:
            print(f"Warning: Invalid memory percentage '{sys.argv[1]}', using default 70%")
    
    if len(sys.argv) > 2:
        try:
            duration_seconds = int(sys.argv[2])
        except ValueError:
            print(f"Warning: Invalid duration '{sys.argv[2]}', using default 60 seconds")
    
    if len(sys.argv) > 3:
        job_id = sys.argv[3]
    
    # Validate inputs
    if memory_percentage < 10 or memory_percentage > 90:
        print(f"Warning: Memory percentage {memory_percentage}% is outside safe range (10-90%), clamping...")
        memory_percentage = max(10, min(90, memory_percentage))
    
    if duration_seconds < 1:
        print(f"Warning: Duration {duration_seconds} is too short, using minimum 1 second")
        duration_seconds = 1
    
    # Create and run the stress tester
    stresser = MemoryStresser(memory_percentage, duration_seconds, job_id)
    stresser.run()


if __name__ == "__main__":
    main()

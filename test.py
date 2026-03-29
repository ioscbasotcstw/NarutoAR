import os
import cv2

def tower_of_hanoi(n, from_rod, to_rod, aux_rod):
    if n == 0:
        return 
    tower_of_hanoi(n - 1, from_rod, aux_rod, to_rod)
    print("Disk", n, " moved from ", from_rod, " to ", to_rod)
    tower_of_hanoi(n - 1, aux_rod, to_rod, from_rod)

if __name__ == "__main__":
    tower_of_hanoi(3, 'A', 'C', 'B')
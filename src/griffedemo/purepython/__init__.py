import math
from typing import Tuple

def solve_quadratic(a: float, b:float, c:float) -> Tuple[float, float]:
    """Will solve the quadratic equation ax^2 + bx + c = 0

    Args:
        a (float): x^2 constant
        b (float): x constant
        c (float): constant

    Returns:
        Tuple[float, float]: The roots of x
    """
    rational = math.sqrt(b**2 - 4 * a * c)
    root1 = (-b + rational) / (2 * a)
    root2 = (-b - rational) / (2 * a)
    return (root1, root2)
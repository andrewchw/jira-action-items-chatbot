"""
Very basic test to check Python syntax
"""
import sys

print("Python is working!")

class TestClass:
    def test_method(self):
        """Test method docstring"""
        a = 1
        if a == 1:
            print("Condition works")
        elif a == 2:
            print("This won't run")
        else:
            print("This won't run either")
            
        # Test indentation with deeper nesting
        for i in range(3):
            if i % 2 == 0:
                print(f"i is even: {i}")
            else:
                print(f"i is odd: {i}")
                
        return "Success"

if __name__ == "__main__":
    tc = TestClass()
    result = tc.test_method()
    print(f"Result: {result}")
    print("Test completed successfully!")
    sys.exit(0)

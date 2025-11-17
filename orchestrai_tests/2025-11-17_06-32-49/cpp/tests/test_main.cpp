```cpp
#include <gtest/gtest.h>
#include <gmock/gmock.h>
#include <memory>
#include <vector>
#include <string>
#include <stdexcept>

// Mock classes and functions for testing
class Calculator {
public:
    virtual ~Calculator() = default;
    virtual int add(int a, int b) const { return a + b; }
    virtual int subtract(int a, int b) const { return a - b; }
    virtual int multiply(int a, int b) const { return a * b; }
    virtual double divide(double a, double b) const {
        if (b == 0.0) {
            throw std::invalid_argument("Division by zero");
        }
        return a / b;
    }
    virtual int factorial(int n) const {
        if (n < 0) throw std::invalid_argument("Negative number");
        if (n == 0 || n == 1) return 1;
        return n * factorial(n - 1);
    }
};

class MockCalculator : public Calculator {
public:
    MOCK_METHOD(int, add, (int a, int b), (const, override));
    MOCK_METHOD(int, subtract, (int a, int b), (const, override));
    MOCK_METHOD(int, multiply, (int a, int b), (const, override));
    MOCK_METHOD(double, divide, (double a, double b), (const, override));
    MOCK_METHOD(int, factorial, (int n), (const, override));
};

class StringProcessor {
public:
    static std::string toUpper(const std::string& str) {
        std::string result = str;
        std::transform(result.begin(), result.end(), result.begin(), ::toupper);
        return result;
    }
    
    static std::string toLower(const std::string& str) {
        std::string result = str;
        std::transform(result.begin(), result.end(), result.begin(), ::tolower);
        return result;
    }
    
    static bool isPalindrome(const std::string& str) {
        std::string cleaned = str;
        cleaned.erase(std::remove_if(cleaned.begin(), cleaned.end(), ::isspace), cleaned.end());
        std::transform(cleaned.begin(), cleaned.end(), cleaned.begin(), ::tolower);
        
        std::string reversed = cleaned;
        std::reverse(reversed.begin(), reversed.end());
        return cleaned == reversed;
    }
    
    static std::vector<std::string> split(const std::string& str, char delimiter) {
        std::vector<std::string> tokens;
        std::stringstream ss(str);
        std::string token;
        
        while (std::getline(ss, token, delimiter)) {
            tokens.push_back(token);
        }
        return tokens;
    }
};

class DataStructures {
public:
    template<typename T>
    static void bubbleSort(std::vector<T>& arr) {
        int n = arr.size();
        for (int i = 0; i < n - 1; i++) {
            for (int j = 0; j < n - i - 1; j++) {
                if (arr[j] > arr[j + 1]) {
                    std::swap(arr[j], arr[j + 1]);
                }
            }
        }
    }
    
    template<typename T>
    static int binarySearch(const std::vector<T>& arr, const T& target) {
        int left = 0;
        int right = arr.size() - 1;
        
        while (left <= right) {
            int mid = left + (right - left) / 2;
            
            if (arr[mid] == target) {
                return mid;
            }
            if (arr[mid] < target) {
                left = mid + 1;
            } else {
                right = mid - 1;
            }
        }
        return -1;
    }
};

// Test Fixtures
class CalculatorTest : public ::testing::Test {
protected:
    void SetUp() override {
        calculator = std::make_unique<Calculator>();
    }
    
    void TearDown() override {
        calculator.reset();
    }
    
    std::unique_ptr<Calculator> calculator;
};

class StringProcessorTest : public ::testing::Test {
protecte
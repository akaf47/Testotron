```cpp
#include <gtest/gtest.h>
#include <gmock/gmock.h>
#include <memory>
#include <string>
#include <vector>
#include <stdexcept>

// Mock classes for testing (since we don't have the actual implementation)
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
};

class StringProcessor {
public:
    virtual ~StringProcessor() = default;
    virtual std::string toUpper(const std::string& str) const {
        std::string result = str;
        std::transform(result.begin(), result.end(), result.begin(), ::toupper);
        return result;
    }
    
    virtual std::string toLower(const std::string& str) const {
        std::string result = str;
        std::transform(result.begin(), result.end(), result.begin(), ::tolower);
        return result;
    }
    
    virtual bool isEmpty(const std::string& str) const {
        return str.empty();
    }
    
    virtual size_t length(const std::string& str) const {
        return str.length();
    }
};

class DataContainer {
private:
    std::vector<int> data;
    
public:
    void addElement(int element) {
        data.push_back(element);
    }
    
    int getElement(size_t index) const {
        if (index >= data.size()) {
            throw std::out_of_range("Index out of range");
        }
        return data[index];
    }
    
    size_t size() const {
        return data.size();
    }
    
    bool empty() const {
        return data.empty();
    }
    
    void clear() {
```cpp
#include <gtest/gtest.h>
#include <gmock/gmock.h>
#include <memory>
#include <vector>
#include <string>
#include <stdexcept>

// Mock classes for testing (since we don't have the actual implementation)
class TestGenerator {
public:
    TestGenerator(const std::string& language) : language_(language) {}
    
    std::string generate(const std::string& sourceCode) {
        return "Generated test for " + language_ + ": " + sourceCode.substr(0, 10);
    }
    
    std::string getLanguage() const { return language_; }
    
private:
    std::string language_;
};

class CodeAnalyzer {
public:
    struct AnalysisResult {
        std::vector<std::string> functions;
        std::vector<std::string> classes;
        int complexity;
    };
    
    AnalysisResult analyzeFile(const std::string& filePath) {
        if (filePath.empty()) {
            throw std::invalid_argument("File path cannot be empty");
        }
        
        AnalysisResult result;
        result.functions = {"function1", "function2"};
        result.classes = {"Class1"};
        result.complexity = 5;
        return result;
    }
    
    bool isValidSourceFile(const std::string& filePath) {
        return filePath.find(".cpp") != std::string::npos ||
               filePath.find(".h") != std::string::npos ||
               filePath.find(".hpp") != std::string::npos;
    }
};

class Testotron {
public:
    struct Config {
        int targetCoverage = 100;
        std::string testFramework = "gtest";
        std::string outputDir = "tests";
    };
    
    Testotron(const Config& config = Config{}) : config_(config) {}
    
    std::vector<std::string> analyzeRepository(const std::string& repoPath) {
        if (repoPath.empty()) {
            throw std::invalid_argument("Repository path cannot be empty");
        }
        
        return {"file1.cpp", "file2.h", "file3.hpp"};
    }
    
    std::string generateTests(const std::vector<std::string>& files) {
        std::string result = "Generated tests for files:\n";
        for (const auto& file : files) {
            result += "- " + file + "\n";
        }
        return result;
    }
    
    struct TestResult {
        int passed = 0;
        int failed = 0;
        double coverage = 0.0;
    };
    
    TestResult runTests(const std::string& testSuite) {
        TestResult result;
        result.passed = 10;
        result.failed = 0;
        result.coverage = 95.5;
        return result;
    }
    
    Config getConfig() const { return config_; }
    
private:
    Config config_;
};

// Test fixtures
class TestGeneratorTest : public ::testing::Test {
protected:
    void SetUp() override {
        cppGenerator = std::make_unique<TestGenerator>("cpp");
        javaGenerator = std::make_unique<TestGenerator>("java");
    }
    
    std::unique_ptr<TestGenerator> cppGenerator;
    std::unique_ptr<TestGenerator> javaGenerator;
};

class CodeAnalyzerTest : public ::testing::Test {
protected:
    void SetUp() override {
        analyzer = std::make_unique<CodeAnalyzer>();
    }
    
    std::unique_ptr<CodeAnalyzer> analyzer;
};

class TestotronTest : public ::testing::Test {
protected:
    void SetUp() override {
        Testotron::Config config;
        config.targetCoverage = 100;
        config.testFramework = "gtest";
        testotron = std::make_
```cpp
#include <gtest/gtest.h>
#include <gmock/gmock.h>
#include <memory>
#include <string>
#include <vector>
#include <map>
#include <stdexcept>

// Mock Testotron class since we don't have the actual implementation
class Testotron {
public:
    struct Config {
        std::string testDirectory = "/tmp/tests";
        std::string outputFormat = "json";
        bool parallelExecution = true;
        int timeout = 30;
    };
    
    struct TestResult {
        int passed = 0;
        int failed = 0;
        int total = 0;
    };
    
    explicit Testotron(const Config& config = Config{}) : config_(config), status_("initialized") {}
    
    TestResult runTests() {
        return TestResult{10, 0, 10};
    }
    
    std::string generateReport() const {
        return "Test Report Generated";
    }
    
    bool validateConfig() const {
        return config_.timeout > 0 && !config_.testDirectory.empty();
    }
    
    bool setupEnvironment() {
        status_ = "ready";
        return true;
    }
    
    bool cleanup() {
        status_ = "cleaned";
        return true;
    }
    
    const std::string& getStatus() const { return status_; }
    const Config& getConfig() const { return config_; }
    
private:
    Config config_;
    std::string status_;
};

// Mock class for testing
class MockTestotron {
public:
    MOCK_METHOD(Testotron::TestResult, runTests, ());
    MOCK_METHOD(std::string, generateReport, (), (const));
    MOCK_METHOD(bool, validateConfig, (), (const));
    MOCK_METHOD(bool, setupEnvironment, ());
    MOCK_METHOD(bool, cleanup, ());
};

class TestotronTest : public ::testing::Test {
protected:
    void SetUp() override {
        defaultConfig_.testDirectory = "/tmp/tests";
        defaultConfig_.outputFormat = "json";
        defaultConfig_.parallelExecution = true;
        defaultConfig_.timeout = 30;
        
        testotron_ = std::make_unique<Testotron>(defaultConfig_);
    }
    
    void TearDown() override {
        testotron_.reset();
    }
    
    Testotron::Config defaultConfig_;
    std::unique_ptr<Testotron> testotron_;
};

// Basic functionality tests
TEST_F(TestotronTest, InitializationWithConfig) {
    EXPECT_EQ(testotron_->getConfig().testDirectory, "/tmp/tests");
    EXPECT_EQ(testotron_->getConfig().outputFormat, "json");
    EXPECT_TRUE(testotron_->getConfig().parallelExecution);
    EXPECT_EQ(testotron_->getConfig().timeout, 30);
    EXPECT_EQ(testotron_->getStatus(), "initialized");
}

TEST_F(TestotronTest, InitializationWithoutConfig) {
    auto emptyTestotron = std::make_unique<Testotron>();
    EXPECT_EQ(emptyTestotron->getStatus(), "initialized");
    EXPECT_EQ(emptyTestotron->getConfig().testDirectory, "/tmp/tests");
}

TEST_F(TestotronTest, RunTestsSuccess) {
    auto result = testotron_->runTests();
    EXPECT_EQ(result.passed, 10);
    EXPECT_EQ(result.failed, 0);
    EXPECT_EQ(result.total, 10);
    EXPECT_EQ(result.total, result.passed + result.failed);
}

TEST_F(TestotronTest, GenerateReport) {
    std::string report = testotron_->generateReport();
    EXPECT_FALSE(report.empty());
    EXPECT_EQ(report, "Test Report Generated");
}

TEST_F(TestotronTest, ValidateConfigValid) {
    EXPECT_TRUE(testotron_->validateConfig());
}

TEST_F(TestotronTest, ValidateConfigInvalid) {
    Testotron::Config invalidConfig;
    invalidConfig.timeout = -1;
    invalidConfig.testDirectory = "";
    
    auto invalidTestotron = std::make_unique<Testotron>(invalidConfig);
    EXPECT_FALSE(invalidTestotron->validateConfig());
}

TEST_F(TestotronTest, SetupEnvironment) {
    EXPECT_TRUE(testotron_->setupEnvironment());
    EXPECT_EQ(testotron_->getStatus(), "ready");
}

TEST_F(TestotronTest, Cleanup) {
    EXPECT_TRUE(testotron_->cleanup());
    EXPECT_EQ(testotron_->getStatus(), "cleaned");
}

// Parameterized tests
class TestotronParameterizedTest : public ::testing::TestWithParam<std::tuple<int, bool, std::string>> {
protected:
    void SetUp() override {
        auto params = GetParam();
        config_.timeout = std::get<0>(params);
        config_.parallelExecution = std::get<1>(params);
        config_.outputFormat = std::get<2>(params);
        config_.testDirectory = "/tmp/param_tests";
    }
    
    Testotron::Config config_;
};

TEST_P(TestotronParameterizedTest, VariousConfigurations) {
    auto testotron = std::make_unique<Testotron>(config_);
    EXPECT_EQ(testotron->getConfig().timeout, config_.timeout);
    EXPECT_EQ(testotron->getConfig().parallelExecution, config_.parallelExecution);
    EXPECT_EQ(testotron->getConfig().outputFormat, config_.outputFormat);
}

INSTANTIATE_TEST_SUITE_P(
    ConfigVariations,
    TestotronParameterizedTest,
    ::testing::Values(
        std::make_tuple(10, true, "json"),
        std::make_tuple(60, false, "xml"),
        std::make_tuple(30, true, "html"),
        std::make_tuple(120, false, "json")
    )
);

// Integration tests
class TestotronIntegrationTest : public ::testing::Test {
protected:
    void SetUp() override {
        config_.testDirectory = "/tmp/integration_tests";
        testotron_ = std::make_unique
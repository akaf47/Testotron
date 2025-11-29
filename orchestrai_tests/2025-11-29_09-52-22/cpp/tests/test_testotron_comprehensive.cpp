```cpp
#include <gtest/gtest.h>
#include <gmock/gmock.h>
#include <string>
#include <vector>
#include <memory>
#include <fstream>
#include <filesystem>

// Mock classes for Testotron components
class TestotronCore {
public:
    TestotronCore(const std::string& repoUrl = "", const std::string& localPath = "") 
        : repo_url_(repoUrl), local_path_(localPath) {}
    
    bool cloneRepository() {
        if (repo_url_.empty()) return false;
        return true;
    }
    
    std::vector<std::string> analyzeRepository() {
        return {"python", "cpp", "java", "javascript"};
    }
    
    bool generateTests() {
        return true;
    }
    
    int runTests() {
        return 0; // Success
    }
    
    std::string getRepoUrl() const { return repo_url_; }
    std::string getLocalPath() const { return local_path_; }

private:
    std::string repo_url_;
    std::string local_path_;
};

class FileAnalyzer {
public:
    static std::string detectLanguage(const std::string& filePath) {
        size_t dotPos = filePath.find_last_of('.');
        if (dotPos == std::string::npos) return "unknown";
        
        std::string extension = filePath.substr(dotPos);
        if (extension == ".cpp" || extension == ".cc" || extension == ".cxx") return "
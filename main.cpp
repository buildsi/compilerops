#include <iostream>
#include <chrono>

using namespace std;

int main() {

    auto start = std::chrono::high_resolution_clock::now();
    int totalI = 0;
    int totalJ = 0;
    for (int i = 1; i <= 1000; ++i) {
        for (int j = 1; j <= 10; ++j) {
            totalI += i;
            totalJ += j; 
        }
    }
    auto stop = std::chrono::high_resolution_clock::now();
    std::chrono::duration<double, std::milli> ms_double = stop - start;
    std::cout << ms_double.count() << std::endl;
    return 0;
}

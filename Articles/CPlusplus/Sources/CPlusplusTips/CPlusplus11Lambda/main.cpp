// C++11 のラムダ式のサンプル
// 記事: Articles/CPlusplus/CPlusplus11-lambda.md

#include <algorithm>
#include <cstdlib>
#include <iostream>
#include <vector>

namespace {

// 得点の一覧 (すべての例で使う)
std::vector<int> MakeScores()
{
    return { 85, 42, 73, 60, 91, 55 };
}

// 例 1. 関数ポインターで条件を渡す
// しきい値は関数の中に固定されていて、呼ぶ側から変えられない
bool IsPassing(int score)
{
    return score >= 60;
}

void CountWithFunctionPointer()
{
    const std::vector<int> scores = MakeScores();

    // 関数名を渡すと、関数ポインターとして渡される
    auto count = std::count_if(scores.begin(), scores.end(), IsPassing);
    std::cout << "function pointer: " << count << " scores >= 60\n";
}

// 例 2. 関数オブジェクトで、しきい値を持たせる
// しきい値をメンバー変数に持ち、operator() で比べる
class AtLeast
{
public:
    explicit AtLeast(int threshold) : threshold_(threshold) {}

    bool operator()(int score) const { return score >= threshold_; }

private:
    int threshold_;
};

void CountWithFunctionObject(int threshold)
{
    const std::vector<int> scores = MakeScores();

    // しきい値を渡して作ったオブジェクトを、関数のように呼んでもらう
    auto count = std::count_if(scores.begin(), scores.end(), AtLeast(threshold));
    std::cout << "function object : " << count << " scores >= " << threshold << '\n';
}

// 例 3. ラムダ式で、しきい値をキャプチャーする
void CountWithLambda(int threshold)
{
    const std::vector<int> scores = MakeScores();

    // [threshold] で、外の変数 threshold を値で取り込む。
    // 条件を、使う場所にその場で書ける
    auto count = std::count_if(scores.begin(), scores.end(),
                               [threshold](int score) { return score >= threshold; });
    std::cout << "lambda          : " << count << " scores >= " << threshold << '\n';
}

// 例 4. 値のキャプチャーは、作った時点の値を使う
void CaptureByValueAndByReference()
{
    const std::vector<int> scores = MakeScores();
    int threshold = 60;

    auto byValue     = [threshold](int score) { return score >= threshold; };  // 60 をコピーして持つ
    auto byReference = [&threshold](int score) { return score >= threshold; }; // 変数 threshold を参照する

    threshold = 80; // ラムダ式を作ったあとで、しきい値を変える

    std::cout << "captured by value    : "
              << std::count_if(scores.begin(), scores.end(), byValue) << " scores\n";     // 60 のまま
    std::cout << "captured by reference: "
              << std::count_if(scores.begin(), scores.end(), byReference) << " scores\n"; // 80 になる
}

// 例 5. 参照のキャプチャーで、結果を外の変数に集める
void SumWithReferenceCapture()
{
    const std::vector<int> scores = MakeScores();
    int total = 0;
    int count = 0;

    // 参照で取り込んだ total と count を、ラムダ式の中から書き換える
    std::for_each(scores.begin(), scores.end(), [&total, &count](int score) -> void {
        total += score;
        ++count;
    });
    std::cout << "total: " << total << ", count: " << count << '\n';
}

// 例 6. キャプチャーしないラムダ式は、関数ポインターに変換できる
void SortWithQsort()
{
    std::vector<int> scores = MakeScores();

    // std::qsort が要求する比較関数の型 int (*)(const void*, const void*) に、
    // 同じシグネチャーのラムダ式を代入する (キャプチャーしないので変換できる)
    int (*compare)(const void*, const void*) = [](const void* left, const void* right) -> int {
        const int lhs = *static_cast<const int*>(left);
        const int rhs = *static_cast<const int*>(right);
        return (lhs > rhs) - (lhs < rhs); // 小さい順に並べる
    };
    std::qsort(scores.data(), scores.size(), sizeof(int), compare);

    std::cout << "sorted:";
    for (int score : scores)
        std::cout << ' ' << score;
    std::cout << '\n';
}

} // namespace

int main()
{
    CountWithFunctionPointer();
    CountWithFunctionObject(80);
    CountWithLambda(80);
    CaptureByValueAndByReference();
    SumWithReferenceCapture();
    SortWithQsort();
}

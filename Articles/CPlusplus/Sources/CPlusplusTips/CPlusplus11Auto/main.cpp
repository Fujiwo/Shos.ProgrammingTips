// C++11 の auto のサンプル
// 記事: Articles/CPlusplus/CPlusplus11-auto.md

#include <iostream>
#include <map>
#include <string>
#include <vector>

namespace {

// 名前ごとの得点の履歴 (例 1・例 2 で使う)
std::map<std::string, std::vector<int>> MakeScoreHistory()
{
    return { { "Alice", { 80, 95 } }, { "Bob", { 72 } } };
}

// 名前ごとの最新の得点 (例 3〜例 5 で使う)
std::map<std::string, int> MakeLatestScores()
{
    return { { "Alice", 80 }, { "Bob", 72 } };
}

// 例 1. auto を使わずに、イテレーターの型を書く
void FindWithExplicitType()
{
    const std::map<std::string, std::vector<int>> scoreHistory = MakeScoreHistory();

    // 型名を省かずに書くと、コンテナーの型をまるごと繰り返すことになる
    std::map<std::string, std::vector<int>>::const_iterator it = scoreHistory.find("Alice");
    if (it != scoreHistory.end())
        std::cout << it->first << " has " << it->second.size() << " scores\n";
}

// 例 2. auto でイテレーターを受ける
void FindWithAuto()
{
    const std::map<std::string, std::vector<int>> scoreHistory = MakeScoreHistory();

    // 型は find の戻り値からコンパイラーが推論する (const_iterator になる)
    auto it = scoreHistory.find("Alice");
    if (it != scoreHistory.end())
        std::cout << it->first << " has " << it->second.size() << " scores\n";
}

// 例 3. 型を書き間違えると、気付かないうちにコピーが作られる
void BindWithWrongType()
{
    std::map<std::string, int> scores = MakeLatestScores();
    auto it = scores.find("Alice");

    // 要素の本当の型は std::pair<const std::string, int>。
    // const の抜けた型で受けると、変換で作られた一時オブジェクトを参照してしまう
    const std::pair<std::string, int>& entry = *it;

    std::cout << std::boolalpha
              << "explicit type refers to the element: " << (&entry.second == &it->second) << '\n';
}

// 例 4. const auto& なら、要素そのものを参照できる
void BindWithAuto()
{
    std::map<std::string, int> scores = MakeLatestScores();
    auto it = scores.find("Alice");

    // 型は *it から推論されるので、要素の型と食い違わない
    const auto& entry = *it;

    std::cout << std::boolalpha
              << "const auto& refers to the element: " << (&entry.second == &it->second) << '\n';
}

// 例 5. auto は参照を落とす
void ModifyThroughAuto()
{
    std::map<std::string, int> scores = MakeLatestScores();

    auto copied = scores["Alice"];      // int (値のコピー)
    copied += 10;                       // コピーが変わるだけで、マップの値は変わらない
    std::cout << "after auto : " << scores["Alice"] << '\n';

    auto& referenced = scores["Alice"]; // int& (マップの値への参照)
    referenced += 10;                   // マップの値が変わる
    std::cout << "after auto&: " << scores["Alice"] << '\n';
}

} // namespace

int main()
{
    FindWithExplicitType();
    FindWithAuto();
    BindWithWrongType();
    BindWithAuto();
    ModifyThroughAuto();
}

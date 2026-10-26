// C++11 のムーブの使い方のサンプル
// 記事: Articles/CPlusplus/CPlusplus11-move-2-usage.md

#include <cstddef>
#include <iostream>
#include <string>
#include <utility>
#include <vector>

namespace {

// 文書の行の一覧 (例 1・例 4 で使う)
std::vector<std::string> MakeLines()
{
    std::vector<std::string> lines;
    lines.push_back("Move semantics were introduced in C++11.");
    lines.push_back("A move hands over the contents instead of copying them.");
    lines.push_back("std::move only casts its argument to an rvalue.");
    return lines;
}

// 例 1. ムーブすると、配列を複製せずに引き継ぐ
void CopyAndMove()
{
    std::vector<std::string> original = MakeLines();
    const std::string* originalArray = original.data(); // 要素を並べた配列の先頭

    // コピー: 要素をすべて複製した、別の配列を持つ
    std::vector<std::string> copied = original;
    std::cout << std::boolalpha
              << "copy: same array = " << (copied.data() == originalArray) << '\n';

    // ムーブ: original の配列を、そのまま引き継ぐ
    std::vector<std::string> moved = std::move(original);
    std::cout << "move: same array = " << (moved.data() == originalArray) << '\n';
    // original の値は未規定になったので、このあとは使わない
}

// 例 2. 関数から、値で返す
// C++03 でよく使われた書き方: 呼ぶ側が用意した vector に、結果を書き込む
void LoadLinesInto(std::vector<std::string>& lines)
{
    lines.push_back("first line");
    lines.push_back("second line");
}

// C++11 からは、値で返しても要素はコピーされない
std::vector<std::string> LoadLines()
{
    std::vector<std::string> lines;
    lines.push_back("first line");
    lines.push_back("second line");
    return lines; // ムーブされるか、コピーそのものが省かれる
}

void ReturnByValue()
{
    std::vector<std::string> filled; // 先に空の変数を用意して、
    LoadLinesInto(filled);           // 中身を書き込んでもらう

    const std::vector<std::string> returned = LoadLines(); // 結果を受け取るだけ。const も付けられる

    std::cout << "output parameter: " << filled.size() << " lines\n";
    std::cout << "return by value : " << returned.size() << " lines\n";
}

// 例 3. コンテナーに、ムーブで入れる
void AddWithMove()
{
    std::vector<std::string> lines;
    for (int number = 1; number <= 3; ++number) {
        std::string line = "Section " + std::to_string(number) + ": how to use move semantics";
        lines.push_back(std::move(line)); // line はこのあと使わないので、中身を引き取ってもらう
    }
    std::cout << lines.size() << " lines, last: " << lines.back() << '\n';
}

// 例 4. 値で受け取り、メンバーにムーブする
class Document
{
public:
    // 引数を値で受け取り、メンバーへムーブする。
    // 呼ぶ側が左辺値を渡せば引数へのコピーが1回、右辺値を渡せばコピーなし
    explicit Document(std::vector<std::string> lines) : lines_(std::move(lines)) {}

    std::size_t LineCount() const { return lines_.size(); }

    // 確認用: メンバーが持つ配列の先頭
    const std::string* LinesData() const { return lines_.data(); }

private:
    std::vector<std::string> lines_;
};

void PassByValueAndMove()
{
    std::cout << std::boolalpha;

    std::vector<std::string> kept = MakeLines();
    const std::string* keptArray = kept.data();
    Document copiedDocument(kept); // kept はこのあとも使うので、そのまま渡す (コピーされる)
    std::cout << "lvalue   : same array = " << (copiedDocument.LinesData() == keptArray) << '\n';

    std::vector<std::string> handed = MakeLines();
    const std::string* handedArray = handed.data();
    Document movedDocument(std::move(handed)); // handed はもう使わないので、ムーブして渡す
    std::cout << "std::move: same array = " << (movedDocument.LinesData() == handedArray) << '\n';

    // 一時オブジェクトを直接渡した場合も、std::move を付けた場合と同じくコピーされない
    Document temporaryDocument(MakeLines());
    std::cout << "temporary: " << temporaryDocument.LineCount() << " lines\n";
}

} // namespace

int main()
{
    CopyAndMove();
    ReturnByValue();
    AddWithMove();
    PassByValueAndMove();
}

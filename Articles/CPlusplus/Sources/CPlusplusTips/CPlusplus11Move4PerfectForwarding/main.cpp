// C++11 の完全転送のサンプル
// 記事: Articles/CPlusplus/CPlusplus11-move-4-perfect-forwarding.md

#include <iostream>
#include <memory>
#include <string>
#include <utility>

namespace {

// 例 1. const 参照で中継すると、右辺値もコピーになる
// 例で作るクラス。名前をコピーで受け取ったか、ムーブで受け取ったかを表示する
class Widget final // 継承を想定しないので、継承を禁じる
{
public:
    explicit Widget(const std::string& name) : name_(name), size_(0) { Show("copied"); }
    explicit Widget(std::string&& name) : name_(std::move(name)), size_(0) { Show("moved"); }
    Widget(const std::string& name, int size) : name_(name), size_(size) { Show("copied"); }
    Widget(std::string&& name, int size) : name_(std::move(name)), size_(size) { Show("moved"); }

private:
    void Show(const char* how) const
    {
        std::cout << "Widget(" << name_ << ", " << size_ << "): name " << how << '\n';
    }

    std::string name_;
    int         size_;
};

template <typename T>
T CreateByConstReference(const std::string& name)
{
    return T(name); // name は const の左辺値なので、いつも const std::string& のコンストラクターが選ばれる
}

void RelayByConstReference()
{
    std::string name = "Alice";
    CreateByConstReference<Widget>(name);               // 変数を渡す
    CreateByConstReference<Widget>(std::string("Bob")); // 一時オブジェクトを渡しても、コピーになる
}

// 例 2. 転送参照と std::forward で、引数をそのまま渡す
template <typename T, typename Arg>
T Create(Arg&& arg) // Arg&& は転送参照。左辺値も右辺値も受け取れる
{
    return T(std::forward<Arg>(arg)); // 左辺値は左辺値のまま、右辺値は右辺値のまま渡す
}

void RelayByForwarding()
{
    std::string name = "Alice";
    Create<Widget>(name);               // 変数 (左辺値) は、コピーになる
    Create<Widget>(std::string("Bob")); // 一時オブジェクト (右辺値) は、ムーブになる
    Create<Widget>(std::move(name));    // std::move を付けた変数も、ムーブになる
    // name はムーブ元なので、このあとは代入するか破棄するだけにする
}

// 例 3. std::forward を書き忘れると、ムーブが途切れる
template <typename T, typename Arg>
T CreateWithoutForward(Arg&& arg)
{
    return T(arg); // 名前の付いた arg は左辺値なので、右辺値を受け取ってもコピーになる
}

void RelayWithoutForward()
{
    CreateWithoutForward<Widget>(std::string("Bob")); // 一時オブジェクトを渡しても、コピーになる
}

// 例 4. 可変引数テンプレートで、いくつの引数もまとめて転送する
// C++14 の std::make_unique と同じ働きをする関数 (C++11 の標準ライブラリには std::make_unique がない)
template <typename T, typename... Args>
std::unique_ptr<T> MakeUnique(Args&&... args) // 引数がいくつでも受け取れる
{
    // 引数の一つひとつを、左辺値か右辺値かを保ったまま、T のコンストラクターに渡す
    return std::unique_ptr<T>(new T(std::forward<Args>(args)...));
}

void RelayVariadicArguments()
{
    std::string name = "Carol";
    std::unique_ptr<Widget> copied = MakeUnique<Widget>(name, 3);                // 名前はコピーになる
    std::unique_ptr<Widget> moved  = MakeUnique<Widget>(std::string("Dave"), 5); // 名前はムーブになる
}

} // namespace

int main()
{
    RelayByConstReference();
    RelayByForwarding();
    RelayWithoutForward();
    RelayVariadicArguments();
}

// C++11 の右辺値参照のサンプル
// 記事: Articles/CPlusplus/CPlusplus11-move-1-rvalue-reference.md

#include <iostream>
#include <string>
#include <utility>

namespace {

// 値で返す関数。呼び出しの結果は一時オブジェクトになる (すべての例で使う)
std::string MakeName()
{
    return "Bob";
}

// 例 1. const 参照は、変数にも一時オブジェクトにも束縛できる
namespace ConstReferenceOnly {

// const std::string& だけを用意する
void Describe(const std::string& text)
{
    std::cout << "const std::string&: " << text << '\n';
}

void CallWithVariableAndTemporary()
{
    std::string name = "Alice";

    Describe(name);       // 変数を渡す
    Describe(MakeName()); // 関数の戻り値 (一時オブジェクト) を渡す
    // どちらも同じ関数が呼ばれ、関数の側からは区別できない
}

} // namespace ConstReferenceOnly

// 例 2. 右辺値参照のオーバーロードで、左辺値と右辺値を区別する
namespace WithRvalueReference {

// 左辺値は、こちらが受け取る
void Describe(const std::string& text)
{
    std::cout << "const std::string&: " << text << '\n';
}

// 右辺値は、こちらが受け取る。呼び出し元がもう使わない値なら、中身を引き取る処理を書ける
void Describe(std::string&& text)
{
    std::cout << "std::string&&     : " << text << '\n';
}

void CallWithVariableAndTemporary()
{
    std::string name = "Alice";

    Describe(name);                 // 変数名だけの式は左辺値
    Describe(MakeName());           // 値で返す関数の戻り値は右辺値
    Describe(std::string("Carol")); // 一時オブジェクトを作る式も右辺値
}

// 例 3. std::move で、変数を右辺値として渡す
void CallWithMove()
{
    std::string name = "Alice";

    // std::move(name) は右辺値なので、std::string&& の方が選ばれる
    Describe(std::move(name));
    // この Describe は中身を引き取らないので、name の値は "Alice" のまま
}

// 例 4. 名前の付いた右辺値参照は、左辺値として扱われる
// text の型は右辺値参照だが、text という名前だけの式は左辺値になる
void Pass(std::string&& text)
{
    Describe(text);            // 左辺値なので、const std::string& の方
    Describe(std::move(text)); // 右辺値として渡し直すと、std::string&& の方
}

void CallPass()
{
    Pass(MakeName());
}

} // namespace WithRvalueReference

} // namespace

int main()
{
    ConstReferenceOnly::CallWithVariableAndTemporary();
    WithRvalueReference::CallWithVariableAndTemporary();
    WithRvalueReference::CallWithMove();
    WithRvalueReference::CallPass();
}

# C++11 のムーブ: 大きなオブジェクトを、コピーせずに受け渡す

C++11 のムーブを紹介します。ムーブを使うと、`std::vector` や `std::string` のようにヒープ上にデータを持つオブジェクトの中身を、複製せずに別のオブジェクトへ移せます。関数から値で返すときや、コンテナーに入れるとき、メンバーに保存するときに、要素のコピーを省けます。

文書の行の一覧 (`std::vector<std::string>`) を例に、コピーとムーブの違いと、ムーブを使う三つの場面を見ていきます。

- 言語: C++11 以降
- 開発環境: Visual Studio 2026 (MSVC v145)。MSVC には `/std:c++11` がないため、`/std:c++14` でビルドした
- 確認: g++ 13.3 の `-std=c++11` でもビルド・実行し、C++11 の範囲に収まっていることを確かめた

※ MSVC で指定できる最も古い C++ の言語標準は C++14 ([/std (言語の標準バージョンの指定)](https://learn.microsoft.com/ja-jp/cpp/build/reference/std-specify-language-standard-version))。

連載「C++11 のムーブ」の2本目です。連載のほかの記事は次のとおりです。

- 1本目: [C++11 の右辺値参照: 左辺値と右辺値で処理を分け、ムーブの土台を作る](CPlusplus11-move-1-rvalue-reference.md)

## これまでの書き方と課題

C++03 では、`std::vector` で別の変数を初期化したり、別のコンテナーに入れたりすると、要素がすべて複製されました。`std::vector<std::string>` なら、文字列一つひとつのバッファーまで複製されます。元の変数をそのあと使わない場合でも、`swap` で中身を入れ替えるような工夫をしない限り、複製は避けられませんでした。

関数から値で返す場合は、戻り値の最適化 (RVO・NRVO) でコピーが省かれることが多くありました。ただし省略は保証されておらず、複数のローカル変数を条件で返し分けるときなど、省略されない場合は要素がすべてコピーされました。そのため、確実にコピーを避けたい場面では、呼ぶ側が用意した変数に結果を書き込む出力引数 (`void LoadLinesInto(std::vector<std::string>& lines)` など) や、`swap` で中身を入れ替える書き方が使われました。

出力引数を使うと、呼ぶ側は先に空の変数を用意しなければならず、結果を入れる変数に `const` も付けられません。関数の宣言を見ても、その引数が入力なのか出力なのかがすぐには分かりません。

## ムーブとは

**ムーブ** (move) は、オブジェクトの中身を別のオブジェクトへ引き継ぐ操作です。元のオブジェクトをもう使わない前提で、複製を省けるところは省きます。何をどう引き継ぐかは型によって決まります。

`std::vector` の要素は、ヒープ上の配列に並んでいます。規格は、アロケーターを別途指定しない `std::vector` のムーブ構築を、要素数によらない定数時間と定めています。要素を一つずつ複製していては定数時間にならないので、主な実装では、配列を指すポインターなどの管理情報だけを引き継ぎ、配列そのものはそのまま使います。

コピーとムーブで、要素を並べた配列の先頭 (`data()` の戻り値) を比べてみます。行の一覧を作る `MakeLines` は、この記事では省いています。

例 1. 「ムーブすると、配列を複製せずに引き継ぐ」

_[C++]_
```cpp
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
```

_[実行結果]_
```text
copy: same array = false
move: same array = true
```

コピーした `copied` は別の配列を持ち、ムーブした `moved` は、`original` が持っていた配列をそのまま使っています。

※ ムーブしたあとも同じ配列を使うことは、規格では明文化されていない。この記事の実行結果 (例 4 を含む) は、g++ 13.3 の標準ライブラリ (libstdc++) でのもの。

ムーブ構築が選ばれるのは、`std::move(original)` で `original` を右辺値として渡しているからです。[右辺値参照の記事](CPlusplus11-move-1-rvalue-reference.md)で説明したとおり、`std::move` は引数を右辺値として扱うキャストで、それ自体は何もムーブしません。右辺値を受け取った `std::vector` のムーブコンストラクターが、中身を引き取ります。

ムーブしたあとの `original` は、有効なオブジェクトですが、値は未規定です。標準ライブラリの型は、別途規定がない限り、ムーブしたあとこの状態になります。

## ムーブの使い方

ムーブを使う場面は、主に次の三つです。

- 関数から値で返す
- もう使わない変数を、`std::move` を付けて渡す
- 値で受け取った引数を、メンバーにムーブする

一つ目は、関数から値で返す場面です。C++03 の出力引数の書き方と並べます。

例 2. 「関数から、値で返す」

_[C++]_
```cpp
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
```

_[実行結果]_
```text
output parameter: 2 lines
return by value : 2 lines
```

C++11 では、`return lines;` のようにローカル変数をそのまま返すと、コピーが省略されない場合でもムーブになります。コピーの省略に頼らなくても、値で返したときに要素がコピーされないので、出力引数を使わずに値で返せます。呼ぶ側は結果を受け取るだけで済み、`const` も付けられます。

※ C++17 では、`return LoadLines();` のように一時オブジェクトを返す場合などで、コピーの省略が保証された。

二つ目は、もう使わない変数を渡す場面です。組み立てた文字列をコンテナーに入れる例で見てみます。

例 3. 「コンテナーに、ムーブで入れる」

_[C++]_
```cpp
void AddWithMove()
{
    std::vector<std::string> lines;
    for (int number = 1; number <= 3; ++number) {
        std::string line = "Section " + std::to_string(number) + ": how to use move semantics";
        lines.push_back(std::move(line)); // line はこのあと使わないので、中身を引き取ってもらう
    }
    std::cout << lines.size() << " lines, last: " << lines.back() << '\n';
}
```

_[実行結果]_
```text
3 lines, last: Section 3: how to use move semantics
```

C++11 の `push_back` には、`const T&` を受け取るものと、`T&&` を受け取るものがあります。`std::move(line)` を渡すと後者が選ばれ、`line` の文字列のバッファーが、コンテナーの要素に引き継がれます。`line` はループの各回で新しく作るので、ムーブしたあとの値を気にする必要はありません。

三つ目は、受け取った値をメンバーに保存する場面です。引数を値で受け取り、メンバーへムーブします。

例 4. 「値で受け取り、メンバーにムーブする」

_[C++]_
```cpp
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
```

_[実行結果]_
```text
lvalue   : same array = false
std::move: same array = true
temporary: 3 lines
```

引数を値で受け取ると、呼ぶ側が渡したものによって、引数の作り方が変わります。左辺値の `kept` を渡すと、引数はコピーで作られ、`kept` はそのまま残ります。`std::move(handed)` を渡すと、引数はムーブで作られます。引数からメンバーへは、どちらの場合もムーブします。そのため、配列が複製されるのは、左辺値を渡したときの1回だけです。

一時オブジェクトの `MakeLines()` を直接渡した場合も右辺値なので、引数はムーブで作られるか、コピーそのものが省かれます。

`const std::vector<std::string>&` と `std::vector<std::string>&&` のコンストラクターを二つ書かなくても、この一つで両方に対応できます。ムーブは1回増えますが、`std::vector` のムーブ構築は定数時間なので、要素数には左右されません。

## ムーブを使うメリット

ムーブを使うと、もう使わないオブジェクトの中身を、要素を複製せずに渡せます。アロケーターを別途指定しない `std::vector` のムーブ構築なら、要素が何万個あっても定数時間で済みます。ムーブ一般の計算量は、型と操作によって異なります。

値で返すことをためらう理由もなくなります。出力引数で書いていた関数を、例 2 の `LoadLines` のように、結果を戻り値で返す形に書けます。

コピーできない型も、ムーブなら、持っている資源 (メモリ、スレッド、ファイルなど) を別のオブジェクトへ移せます。`std::unique_ptr`、`std::thread`、`std::fstream` などは、コピーはできませんが、ムーブはできます。関数から返したり、コンテナーに入れたりできるのは、ムーブのおかげです。

また、`std::move` がコードに残るので、「この変数の中身は、もう引き取ってよい」という意図が読み手にも伝わります。もう使わない大きなオブジェクトを渡すときは、`std::move` を付けることをお勧めします。

## 使うときの注意点

ムーブしたあとの変数の値は、型の保証がない限り当てにしないでください。`std::vector` や `std::string` は、ムーブしたあとも有効なので、代入や `clear()` のように、前提条件のない操作なら使えます。

`std::move` は `const` を取り除きません。`const` の変数に `std::move` を付けると、結果は `const T&&` になり、一般的なムーブコンストラクター `T(T&&)` では受け取れません。そのため、`std::string` のようなコピーできる型ではコピーになり、コピーできない型ではコンパイルエラーになることがあります (詳しくは[右辺値参照の記事](CPlusplus11-move-1-rvalue-reference.md))。

ローカル変数を返すときは、`return std::move(lines);` とは書かないでください。`std::move(lines)` はローカル変数そのものではないので、戻り値の最適化 (NRVO) の対象から外れ、コピーを省略できずに必ずムーブになります。`return lines;` と書けば、ムーブになるか、コピーそのものが省かれます。g++ 13 では、`-Wall` に含まれる `-Wpessimizing-move` が、この書き方を警告します。

`std::string` の短い文字列は、ムーブしてもコピーと変わらないことがあります。主な実装は、短い文字列をヒープではなくオブジェクトの中に持つ (SSO: small string optimization) ので、ムーブしても引き継ぐバッファーがありません。結果は正しいので害はありませんが、短い文字列でムーブの効果を測ろうとしても、差はほとんど出ません。

## まとめ

- ムーブは、オブジェクトの中身を別のオブジェクトへ引き継ぐ操作で、複製を省けるところは省く
- ローカル変数を値で返す、もう使わない変数に `std::move` を付けて渡す、値で受け取った引数をメンバーにムーブする、の三つの場面で使う
- ムーブしたあとの変数は値を当てにせず、使うなら代入のような前提条件のない操作から始める。`return std::move(local);` は書かない

## 参考リンク

- [右辺値参照・ムーブセマンティクス \[N2118\] - cpprefjp C++日本語リファレンス](https://cpprefjp.github.io/lang/cpp11/rvalue_ref_and_move_semantics.html)
- [std::vector::コンストラクタ - cpprefjp C++日本語リファレンス](https://cpprefjp.github.io/reference/vector/vector/op_constructor.html)
- [方法: 移動コンストラクターと移動代入演算子 (C++) の定義](https://learn.microsoft.com/ja-jp/cpp/cpp/move-constructors-and-move-assignment-operators-cpp)
- [/std (言語の標準バージョンの指定)](https://learn.microsoft.com/ja-jp/cpp/build/reference/std-specify-language-standard-version)

# C++11 の右辺値参照: 左辺値と右辺値で処理を分け、ムーブの土台を作る

C++11 の右辺値参照を紹介します。右辺値参照を使うと、渡されたのが呼び出し元でまだ使う変数か、一時オブジェクトのようにもう使わない値かによって、呼び出す関数を分けられます。もう使わない値には、`std::move` を付けて渡した変数も含まれます。そうした値を受け取ったときだけ、コピーせずに中身を引き取る処理を選べるようになります。

文字列を受け取る関数を例に、`const` 参照だけで受け取る書き方と、右辺値参照のオーバーロードを足した書き方を比べます。

- 言語: C++11 以降
- 開発環境: Visual Studio 2026 (MSVC v145)。MSVC には `/std:c++11` がないため、`/std:c++14` でビルドした
- 確認: g++ 13.3 の `-std=c++11` でもビルド・実行し、C++11 の範囲に収まっていることを確かめた

※ MSVC で指定できる最も古い C++ の言語標準は C++14 ([/std (言語の標準バージョンの指定)](https://learn.microsoft.com/ja-jp/cpp/build/reference/std-specify-language-standard-version))。

連載「C++11 のムーブ」の1本目です。

## これまでの書き方と課題

C++03 では、`std::string` のような大きくなりうるオブジェクトを関数に渡すとき、コピーを避けるために `const std::string&` で受け取っていました。`const` 参照は、変数にも一時オブジェクトにも束縛できます。

例で使う `MakeName` は、文字列 `"Bob"` を値で返す関数です (この記事では定義を省いています)。

例 1. 「`const` 参照は、変数にも一時オブジェクトにも束縛できる」

_[C++]_
```cpp
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
```

_[実行結果]_
```text
const std::string&: Alice
const std::string&: Bob
```

変数 `name` を渡しても、`MakeName` の戻り値を渡しても、同じ `Describe` が呼ばれます。関数の側からは、渡されたのが呼び出し元でまだ使う変数なのか、式が終われば破棄される一時オブジェクトなのかを区別できません。

困るのは、受け取った文字列をメンバー変数などに保存する場合です。変数から受け取ったのなら、呼び出し元がまだ使うので、コピーするしかありません。一時オブジェクトなら、中身 (文字列のバッファー) をそのまま引き取っても、ほかに影響しません。ところが `const` 参照からは書き換えられないので、一時オブジェクトでもやはりコピーすることになります。

## 左辺値と右辺値

右辺値参照の説明に入る前に、**左辺値** (lvalue) と **右辺値** (rvalue) の違いを確認しておきます。どちらも、オブジェクトではなく式の分類です。

- 左辺値: `name` のように、変数名だけの式
- 右辺値: `MakeName()` のように値で返す関数の呼び出しや、`std::string("Carol")` のように一時オブジェクトを作る式。後で説明する `std::move(name)` も右辺値

右辺値だからといって、そのオブジェクトをほかから参照していないとは限りません。`std::move(name)` は右辺値ですが、変数 `name` はそのまま残っていて、あとから使えます。

※ C++11 の値のカテゴリーは、さらに xvalue や prvalue などに分かれる。この記事の範囲では、左辺値と右辺値の区別で十分。

## 右辺値参照とは

**右辺値参照** (rvalue reference) は、右辺値に束縛できる参照で、具体的な型 `T` に対して `T&&` と書きます。`const T&` と `T&&` の両方のオーバーロードがあると、`const` でない同じ型の右辺値には `T&&` の方が選ばれます。左辺値は `T&&` に束縛できないので、`const T&` の方が選ばれます。

例 1 の `Describe` に、右辺値参照を受け取るオーバーロードを足してみます。

例 2. 「右辺値参照のオーバーロードで、左辺値と右辺値を区別する」

_[C++]_
```cpp
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
```

_[実行結果]_
```text
const std::string&: Alice
std::string&&     : Bob
std::string&&     : Carol
```

最初の二つは例 1 と同じ呼び出しですが、`MakeName()` の行だけ出力が変わりました。左辺値の `name` は `const std::string&` の方に、右辺値の `MakeName()` と `std::string("Carol")` は `std::string&&` の方に渡っています。

どちらの関数を呼ぶかは、コンパイラーがオーバーロード解決で決めます。ただし、選ばれた関数が実際に中身を引き取るかどうかは、その関数の処理しだいです。例 2 の `Describe` は表示するだけで、何も引き取っていません。

## 右辺値参照の書き方

右辺値参照を受け取るには、引数の型を `T&&` にします。参照の種類ごとに、束縛できる値は次のとおりです。ここでは `T` を `const` でない具体的な型とし、渡す式も同じ型の `const` でないものとします。

| 参照の種類 | 左辺値 (変数名だけの式など) | 右辺値 (一時オブジェクトや `std::move` の結果など) |
|---|---|---|
| `T&` | 束縛できる | 束縛できない |
| `const T&` | 束縛できる | 束縛できる |
| `T&&` | 束縛できない | 束縛できる |

`const T&` はどちらにも束縛できるので、`T&&` のオーバーロードがなければ、右辺値も `const T&` で受け取ります。例 1 がこの状態でした。

※ 関数テンプレートの型引数 `T` に対する `T&&` は、左辺値も受け取れる転送参照 (forwarding reference) という別の仕組み。この表は当てはまらない。

## `std::move` の正体

変数を `T&&` の方の関数に渡したいときには、`<utility>` の `std::move` を使います。

例 3. 「`std::move` で、変数を右辺値として渡す」

_[C++]_
```cpp
void CallWithMove()
{
    std::string name = "Alice";

    // std::move(name) は右辺値なので、std::string&& の方が選ばれる
    Describe(std::move(name));
    // この Describe は中身を引き取らないので、name の値は "Alice" のまま
}
```

_[実行結果]_
```text
std::string&&     : Alice
```

`std::move(name)` は右辺値なので、`std::string&&` の方が選ばれました。

名前に反して、`std::move` それ自体は何もムーブしません。引数を右辺値として扱うキャストで、実装は、引数 `t` を `static_cast<typename std::remove_reference<T>::type&&>(t)` で右辺値参照にキャストして返すだけです (`T` は引数から推論した型)。中身を引き取るのは、`std::move` の結果を受け取った関数の方です。例 3 の `Describe` は表示するだけなので、`name` の値は変わりません。

`std::string` のムーブコンストラクターのように、実際に中身を引き取る関数に渡した場合も、変数 `name` 自体はなくなりません。標準ライブラリの型は、別途規定がない限り、ムーブしたあとも有効ですが、値は未規定になります。代入や `clear()` のように、前提条件のない操作なら、ムーブしたあとでも使えます。

## 右辺値参照を使うメリット

右辺値参照を使うと、左辺値と右辺値で、呼び出す関数を分けられます。左辺値を受け取る関数ではこれまでどおりコピーし、右辺値を受け取る関数では中身を引き取る、という書き分けができます。右辺値の側に渡せるのは一時オブジェクトだけではありません。もう使わない変数も、`std::move` を付ければ渡せます。

`std::string` や `std::vector` のムーブコンストラクター、`push_back` の `T&&` を受け取るオーバーロードなど、標準ライブラリのムーブは、どれもこの仕組みの上に作られています。

## 使うときの注意点

一番間違えやすいのは、右辺値参照型の引数を、さらにほかの関数に渡す場面です。

例 4. 「名前の付いた右辺値参照は、左辺値として扱われる」

_[C++]_
```cpp
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
```

_[実行結果]_
```text
const std::string&: Bob
std::string&&     : Bob
```

`Pass` は右辺値を受け取っていますが、`text` という名前だけの式は左辺値です。そのため、`Describe(text)` は `const std::string&` の方を呼びます。名前の付いた参照は、関数の中で何度でも使えます。名前を使うたびに右辺値として扱われると、最初に渡した先で中身を引き取られ、その後は値が未規定のオブジェクトを使うことになりかねません。そこで言語の規則では、名前の付いた右辺値参照を左辺値として扱います。もう一度右辺値として渡すには、`std::move(text)` と書きます。

もう一つは `const` です。`std::move` は `const` を取り除きません。`const std::string` の変数に `std::move` を付けると、結果は `const std::string&&` になり、`std::string&&` には束縛できません。例 2 の `Describe` なら、`const std::string&` の方が選ばれます。

ムーブ構築でも同じことが起きます。一般的なムーブコンストラクター `T(T&&)` は `const T&&` を受け取れないので、コピーできる型ならコピーコンストラクターが選ばれ、コピーできない型ならコンパイルエラーになることがあります。コピーになってもコンパイルは通るので、ムーブしたつもりでコピーしていても気付きにくい点に注意してください。ムーブしたい変数には、`const` を付けないようにします。

## まとめ

- 左辺値と右辺値は式の分類。変数名だけの式は左辺値、一時オブジェクトを作る式や `std::move` の結果は右辺値
- `const T&` と `T&&` のオーバーロードで、右辺値を渡されたときだけ中身を引き取る処理を選べる
- `std::move` は右辺値として扱うキャストで、それ自体はムーブしない。名前の付いた右辺値参照は左辺値なので、渡し直すときにも `std::move` を付ける

## 参考リンク

- [右辺値参照・ムーブセマンティクス \[N2118\] - cpprefjp C++日本語リファレンス](https://cpprefjp.github.io/lang/cpp11/rvalue_ref_and_move_semantics.html)
- [std::move (utility) - cpprefjp C++日本語リファレンス](https://cpprefjp.github.io/reference/utility/move.html)
- [右辺値参照宣言子: &&](https://learn.microsoft.com/ja-jp/cpp/cpp/rvalue-reference-declarator-amp-amp)
- [値カテゴリ - cppreference.com](https://ja.cppreference.com/w/cpp/language/value_category)
- [/std (言語の標準バージョンの指定)](https://learn.microsoft.com/ja-jp/cpp/build/reference/std-specify-language-standard-version)

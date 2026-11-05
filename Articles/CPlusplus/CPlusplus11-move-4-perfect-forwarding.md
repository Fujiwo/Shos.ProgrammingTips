# 連載「C++11 のムーブ」 その4: 受け取った引数を、左辺値か右辺値かを保ったまま渡す

C++11 の完全転送を紹介します。完全転送を使うと、受け取った引数を別の関数やコンストラクターに中継するときに、左辺値か右辺値かの区別と `const` の有無を保ったまま、引数を渡せます。中継する関数を挟んでも、渡す先で適切なオーバーロードが選ばれ、右辺値ならムーブできます。

名前を受け取るクラス `Widget` を作る関数を例に、`const` 参照で中継する書き方と、転送参照と `std::forward` で中継する書き方を比べます。

- 言語: C++11 以降
- 開発環境: Visual Studio 2026 (MSVC v145)。MSVC には `/std:c++11` がないため、`/std:c++14` でビルドした
- 確認: g++ 13.3 の `-std=c++11` でもビルド・実行し、C++11 の範囲に収まっていることを確かめた

※ MSVC で指定できる最も古い C++ の言語標準は C++14 ([/std (言語の標準バージョンの指定)](https://learn.microsoft.com/ja-jp/cpp/build/reference/std-specify-language-standard-version))。

連載「C++11 のムーブ」の4本目です。連載のほかの記事は次のとおりです。

- 1本目: [連載「C++11 のムーブ」 その1: C++11 の右辺値参照](CPlusplus11-move-1-rvalue-reference.md)
- 2本目: [連載「C++11 のムーブ」 その2: 大きなオブジェクトを、コピーせずに受け渡す](CPlusplus11-move-2-usage.md)
- 3本目: [連載「C++11 のムーブ」 その3: 自作のクラスも、コピーせずに受け渡せるようにする](CPlusplus11-move-3-class.md)

## これまでの書き方と課題

ファクトリー関数のように、受け取った引数を別の関数やコンストラクターに渡すだけの関数があります。C++03 では、こうした関数の引数を、コピーを避けるために `const` 参照で受け取るのが一般的でした。

次の `Widget` は、名前を `const std::string&` で受け取るコンストラクターと、`std::string&&` で受け取るコンストラクターを持ちます。右辺値を受け取ったときは、名前をコピーせずにムーブします。この `Widget` を、`const` 参照で受け取った名前から作ってみます。

例 1. 「`const` 参照で中継すると、右辺値もコピーになる」

_[C++]_
```cpp
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
```

_[実行結果]_
```text
Widget(Alice, 0): name copied
Widget(Bob, 0): name copied
```

一時オブジェクトを渡しても、`CreateByConstReference` の中の `name` は `const` の左辺値なので、`Widget` には右辺値として渡せません。ムーブできるはずの名前が、コピーされています。

右辺値も生かすには、`const std::string&` と `std::string&&` の2通りのオーバーロードを書く方法があります。ただし、引数が2個なら4通り、n 個なら 2 の n 乗通りになり、引数ごとに書き分けるのは現実的ではありません。引数を値で受け取り、`std::move` で渡す方法もあります ([ムーブの使い方の記事](CPlusplus11-move-2-usage.md)の例 4)。渡す先の型が決まっている関数なら、簡単で十分な書き方です。ただし、ムーブ可能な型の右辺値を値で受け取ると、関数の引数を作るためのムーブが1回増えます。コピーもムーブもできない型は値で受け取れません。また、値で受け取る関数テンプレートも書けますが、関数内の引数は左辺値になるため、呼び出し元の引数が左辺値か右辺値かを保てません。そのため、引数の種類を保って中継する汎用関数には向きません。

## 完全転送とは

**完全転送** (perfect forwarding) は、受け取った引数を別の関数に渡すときに、渡された式が左辺値 (lvalue) か右辺値 (rvalue) かの区別と、`const` の有無を保つことです。C++11 では、次の二つを組み合わせて実現します。

- 左辺値も右辺値も受け取れる引数の型 (転送参照)
- 受け取った引数を、元が右辺値だったときだけ右辺値として渡すキャスト (`std::forward`)

## 転送参照

関数テンプレートの引数で、型推論される `T&&` は、右辺値参照ではなく**転送参照** (forwarding reference) になります。[右辺値参照の記事](CPlusplus11-move-1-rvalue-reference.md)で説明したとおり、型推論されない `T&&` (`std::string&&` など) は、右辺値だけを受け取ります。転送参照は、左辺値にも右辺値にも束縛できます。

※ Scott Meyers の呼び方では「ユニバーサル参照」(universal reference)。転送参照は、C++17 の規格で定められた呼び方。

左辺値を渡すと `T` は左辺値参照 (`std::string&` など) に、右辺値を渡すと `T` は参照でない型 (`std::string`) に推論されます。`T` が `std::string&` のとき、引数の型は `std::string& &&` になりますが、参照の参照は、**参照の折りたたみ** (reference collapsing) の規則で `std::string&` になります。`&&` と `&&` の組み合わせだけが右辺値参照になり、`&` を含む組み合わせは左辺値参照になります。

`template <typename T> void Relay(T&& arg)` を呼んだときの推論の結果は、次のとおりです。

| 渡す式 | `T` の推論結果 | `arg` の型 | `std::forward<T>(arg)` |
|---|---|---|---|
| `std::string` の変数 (左辺値) | `std::string&` | `std::string&` | 左辺値 |
| `const std::string` の変数 (左辺値) | `const std::string&` | `const std::string&` | 左辺値 |
| `std::string` の一時オブジェクト (右辺値) | `std::string` | `std::string&&` | 右辺値 |
| `std::move` を付けた `std::string` の変数 (右辺値) | `std::string` | `std::string&&` | 右辺値 |

渡した式が左辺値だったか右辺値だったかは、`T` の推論結果に残ります。この情報を使って、元の式と同じ種類で引数を渡し直すのが `std::forward` です。

## `std::forward` の書き方

`std::forward<T>(arg)` は、`T` が左辺値参照なら `arg` を左辺値として、そうでなければ右辺値として返します。`std::move` がいつも右辺値にするのに対し、`std::forward` は条件付きで右辺値にします。どちらもキャストであり、それ自体はムーブしません。実際にムーブするかどうかは、渡した先の処理によります。

`std::forward` は、`std::move` と同じくヘッダー `<utility>` にあります。`std::move` と違い、テンプレート引数 `<T>` は省けません。式としての `arg` はいつも左辺値なので、引数から推論させると、元が右辺値だったことが分からなくなるためです。

例 1 の `CreateByConstReference` を、転送参照と `std::forward` で書き直します。

例 2. 「転送参照と `std::forward` で、引数をそのまま渡す」

_[C++]_
```cpp
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
```

_[実行結果]_
```text
Widget(Alice, 0): name copied
Widget(Bob, 0): name moved
Widget(Alice, 0): name moved
```

例 1 ではコピーになった `std::string("Bob")` が、ムーブになりました。書いた関数テンプレートは一つだけですが、変数を渡せばコピー、右辺値を渡せばムーブ、と `Widget` のオーバーロードが呼び分けられています。

`std::forward` を書き忘れると、どうなるでしょうか。例 2 との違いは、`return` の行だけです。

例 3. 「`std::forward` を書き忘れると、ムーブが途切れる」

_[C++]_
```cpp
template <typename T, typename Arg>
T CreateWithoutForward(Arg&& arg)
{
    return T(arg); // 名前の付いた arg は左辺値なので、右辺値を受け取ってもコピーになる
}

void RelayWithoutForward()
{
    CreateWithoutForward<Widget>(std::string("Bob")); // 一時オブジェクトを渡しても、コピーになる
}
```

_[実行結果]_
```text
Widget(Bob, 0): name copied
```

右辺値参照の記事で説明したとおり、右辺値参照の変数も、名前が付いていれば左辺値として扱われます。転送参照も同じで、`arg` をそのまま渡すと、いつも左辺値になります。転送参照で受け取った引数は、`std::forward` を付けて渡します。

## 完全転送を使うメリット

完全転送を使うと、引数の種類ごとにオーバーロードを書かなくても、渡す先では、直接呼んだときと同じオーバーロードが選ばれます。中継する関数を挟んでも、右辺値のムーブが途切れません。

可変引数テンプレート (C++11 の、引数の個数を問わないテンプレート) と組み合わせると、いくつの引数でもまとめて転送できます。次の `MakeUnique` は、C++14 で標準ライブラリに入った `std::make_unique` と同じ働きを、配列でない型について行う自作の関数です。

例 4. 「可変引数テンプレートで、いくつの引数もまとめて転送する」

_[C++]_
```cpp
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
```

_[実行結果]_
```text
Widget(Carol, 3): name copied
Widget(Dave, 5): name moved
```

`Widget` の2引数のコンストラクターが呼ばれ、名前は1引数のときと同じく、変数ならコピー、一時オブジェクトならムーブになっています。標準ライブラリの `std::vector` の `emplace_back` や `std::make_shared` も、同じ形で、要素やオブジェクトのコンストラクターに引数を転送しています。

## 使うときの注意点

`T&&` の形をしていても、いつも転送参照になるわけではありません。転送参照になるのは、その関数を呼ぶときに `T` が型推論される場合だけです。`std::vector<T>` のメンバー関数 `push_back(T&&)` の `T` は、`std::vector` の型を決めた時点で決まっているので、右辺値参照です。`const T&&` も、右辺値参照になります。なお、`auto&&` で宣言した変数も、転送参照になります。

同じ引数を、2回以上転送するのは避けてください。1回目の転送先が引数の中身をムーブで引き取ると、2回目にはムーブ元のオブジェクトが渡ります。複数の関数に渡すときは、最後の1回だけを `std::forward` にします。

転送参照を取る関数テンプレートは、ほとんどどんな引数にも合うので、ほかのオーバーロードより優先されやすい点にも注意が必要です。例えば、`const std::string&` を取るオーバーロードと並べると、`const` でない `std::string` の変数を渡したときは、型が完全に一致する転送参照の方が選ばれます。クラスのコンストラクターを転送参照で書くと、`const` でない変数からのコピーでも、コピーコンストラクターではなくこのコンストラクターが選ばれ、意図しない処理やコンパイルエラーになることがあります。転送参照を取る関数は、同じ名前のオーバーロードと並べないのが無難です。

また、「完全」という名前ですが、何でも転送できるわけではありません。波括弧の初期化子リスト (`{1, 2}`) やオーバーロードされた関数の名前は、型推論ができず、コンパイルエラーになります。ヌルポインターのつもりの `0` や `NULL` は整数として推論され、渡す先ではポインターとして扱われません。ヌルポインターには `nullptr` を使ってください。

## まとめ

- 完全転送は、受け取った引数を、左辺値か右辺値かの区別と `const` の有無を保ったまま、別の関数に渡す。転送参照 `T&&` と `std::forward<T>` を組み合わせて書く
- 型推論される `T&&` は転送参照で、左辺値も右辺値も受け取れる。名前の付いた引数は左辺値なので、渡すときは `std::forward` を付ける
- 引数の種類ごとのオーバーロードを書かずに、中継する関数を挟んでもムーブを途切れさせない。`emplace_back` や `std::make_shared` も、この仕組みで引数を転送している
- 同じ引数を2回以上転送しない。転送参照を取る関数は優先されやすいので、同じ名前のオーバーロードと並べない

## 参考リンク

- [右辺値参照・ムーブセマンティクス \[N2118\] - cpprefjp C++日本語リファレンス](https://cpprefjp.github.io/lang/cpp11/rvalue_ref_and_move_semantics.html)
- [std::forward - cpprefjp C++日本語リファレンス](https://cpprefjp.github.io/reference/utility/forward.html)
- [Reference declaration - cppreference.com](https://en.cppreference.com/w/cpp/language/reference.html) の [Reference collapsing](https://en.cppreference.com/w/cpp/language/reference.html#Reference_collapsing) と [Forwarding references](https://en.cppreference.com/w/cpp/language/reference.html#Forwarding_references)
- Scott Meyers『Effective Modern C++ ―C++11/14プログラムを進化させる42項目』(千住治郎 訳、オライリー・ジャパン、ISBN 978-4-87311-736-2) の項目 24〜26 (ユニバーサル参照と `std::forward`)、項目 28 (参照の折りたたみ)、項目 30 (完全転送が失敗する場合)
- [/std (言語の標準バージョンの指定)](https://learn.microsoft.com/ja-jp/cpp/build/reference/std-specify-language-standard-version)

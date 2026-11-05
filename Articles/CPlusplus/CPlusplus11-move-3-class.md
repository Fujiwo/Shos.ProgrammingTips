# 連載「C++11 のムーブ」 その3: 自作のクラスも、コピーせずに受け渡せるようにする

C++11 のムーブコンストラクターとムーブ代入演算子を紹介します。この二つを書くと、自作のクラスも、`std::vector` や `std::string` と同じように、中身を複製せずに別のオブジェクトへ移せます。

ヒープ上に `int` の配列を持つクラス `Buffer` を例に、ムーブ操作の書き方と、`noexcept` を付ける理由を示します。

- 言語: C++11 以降
- 開発環境: Visual Studio 2026 (MSVC v145)。MSVC には `/std:c++11` がないため、`/std:c++14` でビルドした
- 確認: g++ 13.3 の `-std=c++11` でもビルド・実行し、C++11 の範囲に収まっていることを確かめた

※ MSVC で指定できる最も古い C++ の言語標準は C++14 ([/std (言語の標準バージョンの指定)](https://learn.microsoft.com/ja-jp/cpp/build/reference/std-specify-language-standard-version))。

連載「C++11 のムーブ」の3本目です。連載のほかの記事は次のとおりです。

- 1本目: [連載「C++11 のムーブ」 その1: C++11 の右辺値参照](CPlusplus11-move-1-rvalue-reference.md)
- 2本目: [連載「C++11 のムーブ」 その2: 大きなオブジェクトを、コピーせずに受け渡す](CPlusplus11-move-2-usage.md)
- 4本目: [連載「C++11 のムーブ」 その4: 受け取った引数を、左辺値か右辺値かを保ったまま渡す](CPlusplus11-move-4-perfect-forwarding.md)

## これまでの書き方と課題

ヒープ上のメモリを持つクラスは、C++03 では、コピーコンストラクター・コピー代入演算子・デストラクターの三つを自分で書きました。コンパイラーが作るコピーはポインターを写すだけなので、二つのオブジェクトが同じ配列を解放してしまうからです。この三つをそろえて書く決まりは、Rule of Three と呼ばれます。

この書き方では、元のオブジェクトをもう使わない場合も、新しい配列を確保して要素をすべてコピーします。C++11 で `std::move` を付けて渡しても、受け取る側にムーブ操作がなければ、コピーコンストラクターが呼ばれます。

例 1. 「ムーブ操作がないクラスは、右辺値からもコピーする」

_[C++]_
```cpp
// C++03 の書き方: コピー操作とデストラクターを自分で書く (Rule of Three)
// C++03 には final がないので、継承されても正しく破棄されるように、デストラクターを virtual にする。
// ただし、派生クラスのオブジェクトをこのクラスへコピーすると、派生クラスの部分が失われる
// (スライシング) 危険は残る。C++11 からは、final で継承を禁じて防ぐ (例 2 の Buffer)
class CopyOnlyBuffer
{
public:
    explicit CopyOnlyBuffer(std::size_t size) : data_(new int[size]()), size_(size) {}
    CopyOnlyBuffer(const CopyOnlyBuffer& other);            // 配列を確保して、要素をコピーする
    CopyOnlyBuffer& operator=(const CopyOnlyBuffer& other); // 同上
    virtual ~CopyOnlyBuffer() { delete[] data_; }

    std::size_t Size() const { return size_; }

private:
    int*        data_; // ヒープ上の配列。このクラスが解放する
    std::size_t size_;
};

void CopyWithoutMoveOperations()
{
    CopyOnlyBuffer source(1000);
    // std::move で右辺値として渡しても、ムーブ操作がないのでコピーコンストラクターが呼ばれる
    CopyOnlyBuffer destination = std::move(source);
    std::cout << "size = " << destination.Size() << '\n';
}
```

_[実行結果]_
```text
CopyOnlyBuffer: copy constructor
size = 1000
```

コピーコンストラクターとコピー代入演算子の定義は省いています。どちらも、呼ばれたことを表示します。

`CopyOnlyBuffer` はコピー操作とデストラクターを自分で宣言しているので、コンパイラーはムーブ操作を作りません。`std::move(source)` の結果は `const CopyOnlyBuffer&` にも渡せるので、コピーコンストラクターが選ばれます。

## ムーブコンストラクターとは

**ムーブコンストラクター**は、同じ型の右辺値から、中身を引き継いでオブジェクトを作るコンストラクターです。代表的な形は `T(T&&)` です。[右辺値参照の記事](CPlusplus11-move-1-rvalue-reference.md)で説明したとおり、`T&&` は右辺値だけを受け取る参照です。そのため、一時オブジェクトや、`std::move` を付けた変数から作るときに、コピーコンストラクターではなくこちらが選ばれます。

右辺値参照で受け取れたからといって、そのオブジェクトがほかから参照されていないとは限りません。`std::move` を付けた変数は、ムーブしたあとも名前が残っています。ムーブコンストラクターは、引き継いだあとのムーブ元を、デストラクターが安全に動き、代入し直せる有効な状態にしておく必要があります。

`Buffer` の場合は、配列を指すポインターを写して、ムーブ元のポインターを `nullptr` にします。配列そのものはコピーしません。ムーブ代入演算子も考え方は同じで、構築済みのオブジェクトに、右辺値の中身を引き継ぎます。

## ムーブコンストラクターとムーブ代入演算子の書き方

`CopyOnlyBuffer` に、ムーブコンストラクターとムーブ代入演算子を足したのが、次の `Buffer` です。

例 2. 「ムーブコンストラクターとムーブ代入演算子を書く」

_[C++]_
```cpp
// コピー操作・ムーブ操作・デストラクターの五つを書く (Rule of Five)
class Buffer final // 継承を想定しないので、継承を禁じる
{
public:
    explicit Buffer(std::size_t size) : data_(new int[size]()), size_(size) {}
    Buffer(const Buffer& other);
    Buffer& operator=(const Buffer& other);
    Buffer(Buffer&& other) noexcept;            // ムーブコンストラクター
    Buffer& operator=(Buffer&& other) noexcept; // ムーブ代入演算子
    ~Buffer() { delete[] data_; }

    std::size_t Size() const { return size_; }

private:
    int*        data_;
    std::size_t size_;
};

// other の配列を引き取り、other を空にする
Buffer::Buffer(Buffer&& other) noexcept : data_(other.data_), size_(other.size_)
{
    other.data_ = nullptr; // other のデストラクターが、引き取った配列を解放しないように
    other.size_ = 0;
    std::cout << "Buffer: move constructor\n";
}

// 自分の配列を解放してから、other の配列を引き取る
Buffer& Buffer::operator=(Buffer&& other) noexcept
{
    if (this != &other) { // 自分自身からのムーブ代入では、何もしない
        delete[] data_;
        data_ = other.data_;
        size_ = other.size_;
        other.data_ = nullptr;
        other.size_ = 0;
    }
    std::cout << "Buffer: move assignment\n";
    return *this;
}
```

書くときに気を付けるのは、次の四つです。

- 引数は `const` を付けない右辺値参照 (`Buffer&&`) にする。ムーブ元のポインターを書き換えるため
- ムーブ元のポインターを `nullptr` にする。こうしないと、ムーブ元のデストラクターが、引き取った配列を解放してしまう
- ムーブ代入演算子では、先に自分の配列を解放する。`a = std::move(a);` のような自分自身からのムーブ代入では、解放した配列を引き取ることになるので、`this != &other` で確かめる
- 例外を送出しないので、`noexcept` を付ける (理由は後述)

コピー操作・ムーブ操作・デストラクターの五つをそろえて書く決まりは、Rule of Three を広げて Rule of Five と呼ばれます。

例 1 と同じ書き方で、`Buffer` を使ってみます。

例 3. 「ムーブ操作を持つクラスは、右辺値からムーブする」

_[C++]_
```cpp
void MoveWithMoveOperations()
{
    Buffer source(1000);
    Buffer destination = std::move(source); // 例 1 と同じ書き方で、ムーブコンストラクターが呼ばれる
    std::cout << "size = " << destination.Size() << '\n';

    Buffer another(2000);
    destination = std::move(another); // 構築済みの変数には、ムーブ代入演算子が呼ばれる
    std::cout << "size = " << destination.Size() << '\n';
    // source と another はムーブ元なので、このあとは代入するか破棄するだけにする
}
```

_[実行結果]_
```text
Buffer: move constructor
size = 1000
Buffer: move assignment
size = 2000
```

呼ぶ側のコードは例 1 と同じですが、ムーブコンストラクターが選ばれ、1,000個の要素はコピーされていません。ムーブ代入では、`destination` が持っていた配列を解放してから、`another` の配列を引き取っています。

## `noexcept` を付ける理由

`std::vector` は、容量が足りなくなると、より大きな配列を確保し直して、既存の要素を新しい配列へ移します。このとき、要素の型のムーブコンストラクターが例外を送出する可能性があると、途中で例外が出たときに元の状態へ戻せません。そのため、コピーできる型では、ムーブコンストラクターに `noexcept` がなければ、要素をコピーで移すのが一般的です (標準ライブラリの `std::move_if_noexcept` と同じ選び方です)。

コピーできて、ムーブコンストラクターの `noexcept` の有無だけが違う二つの型で、確かめてみます。

例 4. 「コピー可能な型の再確保で、`noexcept` の有無を比べる」

_[C++]_
```cpp
// どちらもコピー可能で、違いはムーブコンストラクターの noexcept の有無だけ
struct ItemWithNoexcept final // 継承を想定しないので、継承を禁じる
{
    ItemWithNoexcept() {}
    ItemWithNoexcept(const ItemWithNoexcept&) { std::cout << "  copy\n"; }
    ItemWithNoexcept(ItemWithNoexcept&&) noexcept { std::cout << "  move\n"; }
};

struct ItemWithoutNoexcept final // 継承を想定しないので、継承を禁じる
{
    ItemWithoutNoexcept() {}
    ItemWithoutNoexcept(const ItemWithoutNoexcept&) { std::cout << "  copy\n"; }
    ItemWithoutNoexcept(ItemWithoutNoexcept&&) { std::cout << "  move\n"; } // noexcept なし
};

// 要素を2個入れた後に容量を増やし、再確保で既存の要素がどう移されるかを表示する
template <typename Item>
void ShowReallocation(const char* typeName)
{
    std::vector<Item> items;
    items.reserve(2);     // 要素を入れる間は、再確保が起きないようにする
    items.emplace_back(); // その場で構築するので、コピーもムーブも起きない
    items.emplace_back();

    std::cout << typeName << ": reserve(capacity() + 1)\n";
    items.reserve(items.capacity() + 1); // 今の容量を超えるので、必ず再確保が起きる
}

void CompareNoexcept()
{
    ShowReallocation<ItemWithNoexcept>("ItemWithNoexcept");
    ShowReallocation<ItemWithoutNoexcept>("ItemWithoutNoexcept");
}
```

_[実行結果]_
```text
ItemWithNoexcept: reserve(capacity() + 1)
  move
  move
ItemWithoutNoexcept: reserve(capacity() + 1)
  copy
  copy
```

`noexcept` を付けた型は、再確保で2個の要素がムーブされ、付けていない型はコピーされました。ムーブコンストラクターを書いても、`noexcept` を付け忘れると、`std::vector` の中では使われないことがあるわけです。ムーブ操作が例外を送出しないなら、`noexcept` を付けてください。

※ コピーできない型では、ムーブコンストラクターに `noexcept` がなくてもムーブで移す。そのムーブが例外を送出した場合、元の状態に戻る保証はなし。

## ムーブ操作を書かずに済ませる (Rule of Zero)

ここまで `Buffer` のムーブ操作を書いてきましたが、まず検討したいのは、自分では書かない方法です。配列を `int*` ではなく `std::vector<int>` のメンバーで持てば、コピー・ムーブ・デストラクターを一つも宣言しなくても、コンパイラーが作る操作が、メンバーの `std::vector` のコピー・ムーブ・デストラクターを呼びます。コンパイラーが作るムーブコンストラクターは、メンバーのムーブコンストラクターがすべて `noexcept` なら、`noexcept` になります。

※ `std::vector` のムーブコンストラクターが規格で `noexcept` と明記されたのは C++17。

リソースの管理を標準ライブラリの型に任せ、五つの操作を自分では宣言しない決まりを、Rule of Zero と呼びます。ムーブ操作を手で書くのは、ポインターやハンドルを直接管理するクラスを作るときに限るのがお勧めです。

## ムーブできるクラスを作るメリット

ムーブ操作を書くと、自作のクラスも、一時オブジェクトや `std::move` を付けた変数から作るときに、配列の確保と要素のコピーを省けます。`noexcept` を付けておけば、`std::vector` の要素にしたときも、再確保のたびに要素をコピーせずに済みます。

関数から値で返すときも、コピーの省略 (RVO・NRVO) に頼らずに、ムーブでコピーを避けられます ([ムーブの使い方の記事](CPlusplus11-move-2-usage.md)を参照)。

また、コピーはできないが持ち主は移せる、というクラスも作れます。ファイルのハンドルを持つクラスなら、コピー操作を `= delete` で削除し、ムーブ操作だけを書けば、ハンドルの持ち主が常に一つに保たれたまま、関数から返したり、コンテナーに入れたりできます。

## 使うときの注意点

デストラクターやコピー操作を自分で宣言すると、ムーブ操作は自動では作られません。例 1 の `CopyOnlyBuffer` のように、`std::move` を付けても、コピーできる型ではコピーになり、コピーできない型ではコンパイルエラーになることがあります。ログを出すためにデストラクターを足しただけでも、ムーブ操作は作られなくなるので注意してください。

メンバーごとのムーブで正しく動くクラスなら、`Buffer(Buffer&&) = default;` のように `= default` で宣言すれば、コンパイラーにムーブ操作を作らせられます。`Buffer` のように生のポインターで配列を所有するクラスでは、メンバーごとのムーブではポインターが写されるだけで、ムーブ元が空になりません。ポインターを引き継いでムーブ元を空にする処理は、自分で書く必要があります。

ムーブ元のオブジェクトは、少なくともデストラクターが安全に動き、代入し直せる状態にしておいてください。`Buffer` では、ポインターを `nullptr` に、要素数を 0 にしています。`delete[]` に `nullptr` を渡しても何も起きないので、デストラクターも代入もそのまま動きます。

## まとめ

- ムーブコンストラクター `T(T&&)` とムーブ代入演算子は、右辺値の中身を引き継ぎ、ムーブ元をデストラクターが安全に動く状態にしておく
- ムーブ操作が例外を送出しないなら `noexcept` を付ける。付けないと、`std::vector` の再確保ではコピーが使われることがある
- まず標準ライブラリの型にリソースの管理を任せ、ムーブ操作を書かずに済ませる (Rule of Zero)。手で書くのは、リソースを直接管理するクラスに限る

## 参考リンク

- [右辺値参照・ムーブセマンティクス \[N2118\] - cpprefjp C++日本語リファレンス](https://cpprefjp.github.io/lang/cpp11/rvalue_ref_and_move_semantics.html)
- [std::vector::reserve - cpprefjp C++日本語リファレンス](https://cpprefjp.github.io/reference/vector/vector/reserve.html)
- [方法: 移動コンストラクターと移動代入演算子 (C++) の定義](https://learn.microsoft.com/ja-jp/cpp/cpp/move-constructors-and-move-assignment-operators-cpp)
- [C++ Core Guidelines](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines) の [C.20](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines#rc-zero) (Rule of Zero)、[C.21](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines#rc-five) (Rule of Five)、[C.66](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines#rc-move-noexcept) (ムーブ操作を `noexcept` にする)
- [/std (言語の標準バージョンの指定)](https://learn.microsoft.com/ja-jp/cpp/build/reference/std-specify-language-standard-version)

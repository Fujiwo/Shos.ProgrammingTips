# C++11 のラムダ式: 関数オブジェクトのクラスを書かずに、処理をその場で渡す

C++11 で入った機能のうち、ラムダ式を紹介します。ラムダ式を使うと、アルゴリズムに渡す処理を、そのアルゴリズムを呼ぶ場所に書けます。周りの変数も取り込めるので、状態を持たせるためだけにクラスを定義する必要がなくなります。

得点の一覧から、しきい値以上の得点を数えるコードを例に、関数ポインター、関数オブジェクト、ラムダ式の三つの書き方を比べます。

- 言語: C++11 以降
- 開発環境: Visual Studio 2026 (MSVC v145)。MSVC には `/std:c++11` がないため、`/std:c++14` でビルドした
- 確認: g++ 13.3 の `-std=c++11` でもビルド・実行し、C++11 の範囲に収まっていることを確かめた

※ MSVC で指定できる最も古い C++ の言語標準は C++14 ([/std (言語の標準バージョンの指定)](https://learn.microsoft.com/ja-jp/cpp/build/reference/std-specify-language-standard-version))。

## これまでの書き方と課題

C++03 までは、`std::count_if` のようなアルゴリズムに条件を渡すとき、関数ポインターか関数オブジェクトを使っていました。得点の一覧 (85、42、73、60、91、55 の6個) は `MakeScores` という関数で用意し、記事では省いています。

まず、関数ポインターで書いてみます。

例 1. 「関数ポインターで条件を渡す」

_[C++]_
```cpp
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
```

_[実行結果]_
```text
function pointer: 4 scores >= 60
```

しきい値の 60 は、`IsPassing` の中に固定されています。`std::count_if` は要素だけを渡して条件を呼ぶので、しきい値を渡す引数がありません。80 以上を数えるには、関数を書き分けるか、グローバル変数に頼ることになります。

しきい値を呼ぶ側で決めるには、関数オブジェクトを使います。

例 2. 「関数オブジェクトで、しきい値を持たせる」

_[C++]_
```cpp
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
```

_[実行結果]_
```text
function object : 2 scores >= 80
```

しきい値は渡せるようになりましたが、条件を一つ渡すために、10行ほどのクラスを書いています。C++03 では、関数の中で定義したクラス (ローカルクラス) をテンプレートの引数にできないので、このクラスは関数の外に置くしかありません。C++11 ではローカルクラスも渡せるようになりましたが、条件一つのためにクラスを定義する手間は変わりません。読み手は、`AtLeast(threshold)` が何を比べるのかを、離れた場所にある定義で確かめることになります。

## ラムダ式とは

ラムダ式は、名前のない関数オブジェクトを、式としてその場で作る機能です。例 2 をラムダ式で書き直すと、次のようになります。

例 3. 「ラムダ式で、しきい値をキャプチャーする」

_[C++]_
```cpp
void CountWithLambda(int threshold)
{
    const std::vector<int> scores = MakeScores();

    // [threshold] で、外の変数 threshold を値で取り込む。
    // 条件を、使う場所にその場で書ける
    auto count = std::count_if(scores.begin(), scores.end(),
                               [threshold](int score) { return score >= threshold; });
    std::cout << "lambda          : " << count << " scores >= " << threshold << '\n';
}
```

_[実行結果]_
```text
lambda          : 2 scores >= 80
```

先頭の `[threshold]` で、外の変数 `threshold` の値を取り込んでいます。これを **キャプチャー** と呼びます。結果は例 2 と同じで、条件は `std::count_if` の呼び出しの中に書かれています。

コンパイラーは、ラムダ式から `operator()` を持つ名前のないクラス (**クロージャー型**) を作り、そのオブジェクトを生成します。キャプチャーした `threshold` はメンバー変数に、ラムダ式の本体は `operator()` の本体になります。例 2 の `AtLeast` とほぼ同じクラスを、コンパイラーが代わりに書いてくれるわけです。

## ラムダ式の書き方

ラムダ式は、次の形で書きます。

_[疑似コード]_
```text
[キャプチャー](引数) -> 戻り値の型 { 本体 }
```

`-> 戻り値の型` は省略できます。C++11 の規格では、本体が `return 式;` の一文だけなら式の型が、それ以外なら `void` が戻り値の型になります。値を返す本体が二つ以上の文からなるときは、戻り値の型を書きます。

※ この制限は C++14 で緩和。g++ 13.3 では、`-std=c++11` でも、二つ以上の文からなる本体から戻り値の型を推論。

キャプチャーには、次の書き方があります。

| 書き方 | 取り込むもの |
|---|---|
| `[]` | 何も取り込まない |
| `[x]` | 変数 `x` のコピー (値のキャプチャー) |
| `[&x]` | 変数 `x` への参照 (参照のキャプチャー) |
| `[=]` | 本体で使う外の変数すべてのコピー |
| `[&]` | 本体で使う外の変数すべてへの参照 |
| `[this]` | メンバー関数の中で、`this` ポインター |

値のキャプチャーは、ラムダ式を作った時点の値をコピーして持ちます。参照のキャプチャーは、呼び出した時点の元の変数を見ます。

例 4. 「値のキャプチャーは、作った時点の値を使う」

_[C++]_
```cpp
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
```

_[実行結果]_
```text
captured by value    : 4 scores
captured by reference: 2 scores
```

`byValue` は作った時点の 60 で比べて4件を、`byReference` は呼び出した時点の 80 で比べて2件を数えます。クロージャー型には名前がないので、ラムダ式を変数に入れるときは `auto` で受けます。

参照のキャプチャーは、ラムダ式の中から外の変数を書き換えたいときにも使います。

例 5. 「参照のキャプチャーで、結果を外の変数に集める」

_[C++]_
```cpp
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
```

_[実行結果]_
```text
total: 406, count: 6
```

本体に `return` がないので、`-> void` を省いても、戻り値の型は `void` になります。ここでは、戻り値の型を書く位置を示すために明示しました。

## ラムダ式を使うメリット

ラムダ式を使うと、条件を、それを使う場所に書けます。例 2 と比べると、クラスの定義がなくなり、何を数えているのかを `std::count_if` の行だけで読み取れます。しきい値のような状態も、キャプチャーで渡せます。アルゴリズムに渡すその場限りの条件は、ラムダ式で書くことをお勧めします。

## 関数ポインター・関数オブジェクトとの比較

ここまでの三つの書き方を、表にまとめます。

| 観点 | 関数ポインター | 関数オブジェクト | ラムダ式 |
|---|---|---|---|
| 状態 (しきい値など) を持てるか | 持てない (グローバル変数などに頼る) | メンバー変数で持てる | キャプチャーで持てる |
| 定義を書く場所 | 名前空間スコープの関数 | クラスの定義が要る | 使う場所に式として書ける |
| 型名を書けるか | 書ける (`bool (*)(int)`) | 書ける (クラス名) | 書けない。`auto`、テンプレート、`std::function` で受ける |
| C の API に渡せるか | API が要求する関数ポインター型に合えば渡せる | 渡せない | キャプチャーせず、API が要求する関数ポインター型に合えば渡せる |

キャプチャーしないラムダ式は、引数と戻り値の型が同じ関数ポインターに変換できます。そのため、`std::qsort` の比較関数のように、関数ポインターを受け取る C の API にも渡せます。キャプチャーするラムダ式は、取り込んだ値を持つので変換できません。

同じ条件をいくつもの関数やファイルで使い回すなら、名前を付けた関数オブジェクトにします。それ以外は、ラムダ式で足ります。

## 使うときの注意点

一番気を付けたいのは、参照でキャプチャーした変数の寿命です。ローカル変数を参照でキャプチャーしたラムダ式を関数から返したり、`std::function` に入れて保存したりすると、関数を抜けたあとに、なくなった変数への参照が残ります。このラムダ式を呼ぶと、未定義動作になります。ラムダ式を作った関数より長く使うときは、値でキャプチャーします。

`this` も同じです。`[this]` で取り込むのは、オブジェクトのコピーではなくポインターです。メンバー関数の中で `[=]` や `[&]` と書いてメンバー変数を使ったときも、`this` が暗黙に取り込まれます。オブジェクトがなくなったあとにラムダ式を呼ぶと、無効なポインターを使うことになります。

もう一つは、読みやすさです。`[=]` や `[&]` でまとめてキャプチャーすると、何を取り込んだのかが、本体を読まないと分かりません。取り込む変数は一つずつ書き、本体が長くなったら名前を付けた関数に切り出すことをお勧めします。

## まとめ

- ラムダ式は、名前のない関数オブジェクトを、式としてその場で作る
- キャプチャーで周りの変数を取り込めるので、状態を持たせるためのクラスが要らない
- 作った関数より長く使うラムダ式は、参照ではなく値でキャプチャーする

C++14 以降では、引数の型に `auto` を使えるジェネリックラムダや、初期化キャプチャーなど、ラムダ式で書けることがさらに増えています。

## 参考リンク

- [ラムダ式 \[N2927\] - cpprefjp C++日本語リファレンス](https://cpprefjp.github.io/lang/cpp11/lambda_expressions.html)
- [C++ でのラムダ式](https://learn.microsoft.com/ja-jp/cpp/cpp/lambda-expressions-in-cpp)
- [/std (言語の標準バージョンの指定)](https://learn.microsoft.com/ja-jp/cpp/build/reference/std-specify-language-standard-version)

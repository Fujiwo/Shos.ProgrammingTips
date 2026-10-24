# C++11 の auto: 長い型名を書かずに、型を正しく受ける

C++11 で入った機能のうち、`auto` を紹介します。「型名を書く手間が省ける機能」と紹介されることが多いのですが、利点はそれだけではありません。変数の型をコンパイラーに推論させると、型の書き間違いによる余計なコピーも防げます。

`std::map` の要素を探して受け取るコードを例に、`auto` を使う前と後を比べます。

- 言語: C++11 以降
- 開発環境: Visual Studio 2026 (MSVC v145)。MSVC には `/std:c++11` がないため、`/std:c++14` でビルドした
- 確認: g++ 13.3 の `-std=c++11` でもビルド・実行し、C++11 の範囲に収まっていることを確かめた

※ MSVC で指定できる最も古い C++ の言語標準は C++14 ([/std (言語の標準バージョンの指定)](https://learn.microsoft.com/ja-jp/cpp/build/reference/std-specify-language-standard-version))。

## これまでの書き方と課題

C++03 までは、変数を宣言するたびに型を書く必要がありました。標準ライブラリのコンテナのイテレーターでは、この型名がかなり長くなります。次は、名前ごとの得点の履歴を `std::map` に入れておき、`"Alice"` の得点を探す例です。データを用意する部分は `MakeScoreHistory` という関数にまとめ、記事では省いています。

例 1. 「auto を使わずに、イテレーターの型を書く」

_[C++]_
```cpp
void FindWithExplicitType()
{
    const std::map<std::string, std::vector<int>> scoreHistory = MakeScoreHistory();

    // 型名を省かずに書くと、コンテナの型をまるごと繰り返すことになる
    std::map<std::string, std::vector<int>>::const_iterator it = scoreHistory.find("Alice");
    if (it != scoreHistory.end())
        std::cout << it->first << " has " << it->second.size() << " scores\n";
}
```

`find` の戻り値を受けるだけのために、コンテナの型をまるごと繰り返しています。読みにくいうえに、コンテナの型を `std::unordered_map` などに変えると、宣言の行に加えて、この行も直さなければなりません。

もっと困るのは、型を書き間違えてもコンパイルが通ってしまう場合があることです。これは「auto を使うメリット」の節で、実際に確かめます。

## auto とは

`auto` は、変数の型を初期化式からコンパイラーに推論させる指定です。例 1 を `auto` で書き直すと、次のようになります。

例 2. 「auto でイテレーターを受ける」

_[C++]_
```cpp
void FindWithAuto()
{
    const std::map<std::string, std::vector<int>> scoreHistory = MakeScoreHistory();

    // 型は find の戻り値からコンパイラーが推論する (const_iterator になる)
    auto it = scoreHistory.find("Alice");
    if (it != scoreHistory.end())
        std::cout << it->first << " has " << it->second.size() << " scores\n";
}
```

`it` の型は、`find` の戻り値の型から決まります。`scoreHistory` は `const` なので、`find` は `const_iterator` を返し、`it` も `const_iterator` になります。型は例 1 と同じで、実行結果も変わりません。コンテナの型を `std::unordered_map` などに変えても、この行は直さずに済みます。

_[実行結果]_
```text
Alice has 2 scores
```

推論はコンパイル時に行われ、`it` の型はそこで一つに決まります。静的型付けのままで、実行時に型が変わる変数になるわけではありません。

※ C++03 までの `auto` は、自動変数を表す記憶域クラス指定子。C++11 で、型推論のためのキーワードに変更。

## auto の書き方

`auto` は、型名の代わりに書きます。`&` や `const` と組み合わせると、受け方を指定できます。

| 書き方 | 推論される型 (初期化式が `int&` を返すとき) | 用途 |
|---|---|---|
| `auto x = 式;` | `int` | 値をコピーして受ける |
| `auto& x = 式;` | `int&` | 元のオブジェクトを参照し、変更もする |
| `const auto& x = 式;` | `const int&` | 元のオブジェクトを参照し、読むだけにする |

`auto` だけを書くと、初期化式が参照を返していても、推論される型から参照と最上位の `const` が外れます。元のオブジェクトを参照したいときは、`auto&` か `const auto&` と書きます。この違いでつまずく例は、「使うときの注意点」の節で取り上げます。

## auto を使うメリット

`auto` には、型名を書かずに済むことのほかに、型の書き間違いを防げるというメリットがあります。

ここからは、名前ごとの最新の得点だけを持つ `std::map<std::string, int>` を使います。データは `MakeLatestScores` という関数で用意します。

このマップの要素の型は、`std::pair<const std::string, int>` です。マップのキーは書き換えられないので、`const` が付いています。この `const` を書き忘れて要素を受けると、どうなるでしょうか。

例 3. 「型を書き間違えると、気付かないうちにコピーが作られる」

_[C++]_
```cpp
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
```

_[実行結果]_
```text
explicit type refers to the element: false
```

`entry` は、マップの要素を参照していません。`std::pair` は、要素の型が変換できる別の `pair` から作れます。また、`const` の付いた参照は一時オブジェクトにも束縛できます。そのため、コンパイラーは要素を `std::pair<std::string, int>` に変換した一時オブジェクトを作り、`entry` をそこに束縛します。このときキーの文字列もコピーされますが、エラーにはなりません。g++ で `-Wall -Wextra` を指定しても、警告は出ませんでした。

`const auto&` で受ければ、この問題は起きません。

例 4. 「const auto& なら、要素そのものを参照できる」

_[C++]_
```cpp
void BindWithAuto()
{
    std::map<std::string, int> scores = MakeLatestScores();
    auto it = scores.find("Alice");

    // 型は *it から推論されるので、要素の型と食い違わない
    const auto& entry = *it;

    std::cout << std::boolalpha
              << "const auto& refers to the element: " << (&entry.second == &it->second) << '\n';
}
```

_[実行結果]_
```text
const auto& refers to the element: true
```

`entry` の型は `*it` から推論されて `const std::pair<const std::string, int>&` になり、マップの要素そのものを参照します。`const auto&` で受ければ、要素の型はコンパイラーが決めるので、`const` を書き忘れる余地がありません。`auto` を勧める一番の理由は、ここにあります。

## 使うときの注意点

`auto` は参照を外して推論するので、参照のつもりで `auto` と書くと、値のコピーを変更することになります。

例 5. 「auto は参照を落とす」

_[C++]_
```cpp
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
```

_[実行結果]_
```text
after auto : 80
after auto&: 90
```

`copied` は `int` のコピーなので、10 を足してもマップの値は 80 のままです。マップの値を書き換えるには、`auto&` で受けます。

波括弧で初期化するときにも、注意が必要です。`auto values = {1, 2, 3};` のように `=` と波括弧を組み合わせると、`values` の型は `std::initializer_list<int>` になります。要素が一つの `auto x = {1};` でも同じで、`x` は `int` になりません。`int` として受けたいときは、`auto x = 1;` と書きます。

※ `=` のない `auto x{1};` の型は、C++11 の規格では `std::initializer_list<int>`。C++17 で採用された N3922 で `int` に変更。g++ 13.3 は `-std=c++11` でも `int` と推論する。

最後の注意点は、読みやすさです。`auto result = Calculate();` のように、右辺を見ても型が分からない箇所で `auto` を使うと、読み手は `Calculate` の宣言まで型を調べに行くことになります。お勧めの使い分けは、次のとおりです。

- 使う: イテレーターのように、型が長く、右辺から型が明らかな箇所
- 使う: 例 3 のように、型を書き間違えやすい箇所
- 型を書く: 型そのものが、読み手に必要な情報である箇所

## まとめ

- `auto` は、変数の型を初期化式からコンパイル時に推論する。静的型付けはそのまま
- 長い型名を書かずに済み、型の書き間違いによる余計なコピーも防げる
- 参照で受けたいときは `auto&`、読むだけなら `const auto&` と書く

C++14 以降では、関数の戻り値の型の推論など、`auto` を使える場所がさらに増えています。

## 参考リンク

- [変数の型推論のためのauto \[N1984\] - cpprefjp C++日本語リファレンス](https://cpprefjp.github.io/lang/cpp11/auto.html)
- [/std (言語の標準バージョンの指定)](https://learn.microsoft.com/ja-jp/cpp/build/reference/std-specify-language-standard-version)

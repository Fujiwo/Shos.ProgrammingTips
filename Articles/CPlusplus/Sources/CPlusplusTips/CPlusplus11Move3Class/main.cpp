// C++11 のムーブできるクラスの書き方のサンプル
// 記事: Articles/CPlusplus/CPlusplus11-move-3-class.md

#include <algorithm>
#include <cstddef>
#include <iostream>
#include <utility>
#include <vector>

namespace {

// 例 1. ムーブ操作がないクラスは、右辺値からもコピーする
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

// 例 2. ムーブコンストラクターとムーブ代入演算子を書く
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

// 例 3. ムーブ操作を持つクラスは、右辺値からムーブする
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

// 例 4. コピー可能な型の再確保で、noexcept の有無を比べる
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

// 以下は記事では省略: コピー操作の定義
// このサンプルで呼ばない定義もあるので、未使用の警告が出ないように inline にする
inline CopyOnlyBuffer::CopyOnlyBuffer(const CopyOnlyBuffer& other)
    : data_(new int[other.size_]), size_(other.size_)
{
    std::copy(other.data_, other.data_ + other.size_, data_);
    std::cout << "CopyOnlyBuffer: copy constructor\n";
}

inline CopyOnlyBuffer& CopyOnlyBuffer::operator=(const CopyOnlyBuffer& other)
{
    if (this != &other) {
        int* const copiedData = new int[other.size_]; // 確保に失敗しても、自分の状態を変えない
        std::copy(other.data_, other.data_ + other.size_, copiedData);
        delete[] data_;
        data_ = copiedData;
        size_ = other.size_;
    }
    std::cout << "CopyOnlyBuffer: copy assignment\n";
    return *this;
}

inline Buffer::Buffer(const Buffer& other) : data_(new int[other.size_]), size_(other.size_)
{
    std::copy(other.data_, other.data_ + other.size_, data_);
    std::cout << "Buffer: copy constructor\n";
}

inline Buffer& Buffer::operator=(const Buffer& other)
{
    if (this != &other) {
        int* const copiedData = new int[other.size_]; // 確保に失敗しても、自分の状態を変えない
        std::copy(other.data_, other.data_ + other.size_, copiedData);
        delete[] data_;
        data_ = copiedData;
        size_ = other.size_;
    }
    std::cout << "Buffer: copy assignment\n";
    return *this;
}

} // namespace

int main()
{
    CopyWithoutMoveOperations();
    MoveWithMoveOperations();
    CompareNoexcept();
}

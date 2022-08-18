# 配平化学方程式

## 基本原理

将化学方程式转化为系数矩阵，配平即为求系数矩阵所蕴含的齐次方程组的非平凡解。存在非平凡解的充要条件是矩阵的列数减去矩阵的秩（即零空间的维数）大于零。非平凡解若存在即为无穷多个，但线性无关的非平凡解的数目一定为零空间的维数。要想求得线性无关的非平凡解，只需通过高斯消元法得到零空间的一组基即可。

## 限制条件

配平方程式，除了不能是平凡解，解的每个元素还必须至少为 1。因此上文求得的解的数目（可能）只是实际解数目的上界。目前我还没办法证明零空间的维数同时也是实际解数目的下界，也不知道如何通过零空间的一组基通过基变换求出满足配平条件的一组配平系数，甚至不知道是否存在这样的基变换。实际运行中只能说，如果*碰巧*基的系数都至少为 1，那么就算求出所有线性无关的配平系数；如果有些基的系数非正，那么只能舍去它们，求出一部分配平系数。

## 实现方法

我使用状态机解析形如 `H2 + O2 = H2O` 的化学方程式为系数矩阵。我使用[全选主元法](https://math.stackexchange.com/questions/1334983/gauss-elimination-difference-between-partial-and-complete-pivoting)实现高斯消元法，得到行最简形并顺便得到矩阵的秩。高斯消元法由 Cython 实现。

## 使用

准备工作：

```bash
# 建立虚拟环境（可选）
#python3 -m virtualenv rt
#. rt/bin/activate

# 下载依赖并编译 Cython 模块
pip3 install -r requirements.txt
python setup.py build_ext --inplace
```

使用范例：

```bash
(rt) $ python3 solveeq.py H2 + O2 = H2O
2 1 2
(rt) $ python3 solveeq.py NH3 + H2S = "(NH4)2S"
2 1 1
(rt) $ python3 solveeq.py P4 + P2I4 + H2O = PH4I + H3PO4
13 10 128 40 32
(rt) $ python3 solveeq.py XeF4 + H2O = XeO3 + Xe + O2 + HF
0 0 -2 2 3 0
3 6 2 1 0 12
```

其中最后一个最多有两种（线性无关的）配平方式，但用现有方法无法一般性地找出来。

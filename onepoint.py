from xianhuo import SpotTrader
import keyboard  # 用于读取箭头键
from future import futureSystem


def main():
    xianhuo= SpotTrader()
    heyue= futureSystem()
    xianhuo.change_connect()
    heyue.change_connect()

    # 打印提示信息
    print("请按 ↑ 表示现货开多，↓ 表示现货开空")
    # 无限循环，直到检测到 ↑ 或 ↓ 键
    while True:
        # 检测是否按下了 ↑ 键
        if keyboard.is_pressed("up"):
            # 打印提示信息
            print("检测到 ↑：开多 (Bid)")
            # 调用 listen_trade_direction1 函数，传入参数 "Bid"
            xianhuo.listen_trade_direction1("Bid")
            heyue.listen_trade_direction1("Ask")
            # 跳出循环
            break
        # 检测是否按下了 ↓ 键
        elif keyboard.is_pressed("down"):
            # 打印提示信息
            print("检测到 ↓：开空 (Ask)")
            # 调用 listen_trade_direction1 函数，传入参数 "Ask"
            xianhuo.listen_trade_direction1("Ask")
            heyue.listen_trade_direction1("Bid")
            # 跳出循环
            break

        
    # 无限循环，直到输入了0.01到0.99之间的数字
    while True:
        # 输入资金比例
            ratio = input("请输入资金比例：")
        # 将输入的字符串转换为浮点数
            ratio = float(ratio)
        # 判断输入的数字是否在0.01到0.99之间
            if ratio >= 0.01 and ratio <= 0.99:
            # 调用 change_ratio 函数，传入参数 ratio
                xianhuo.change_ratio(ratio)
                heyue.change_ratio(ratio)
            # 打印提示信息
                print("资金比例已设置为：", ratio)
                break
            else:
                print("请输入0.01到0.99之间的数字")
        
    
    xianhuo.main()
    heyue.main()



main()
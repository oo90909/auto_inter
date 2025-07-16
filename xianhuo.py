import base64
import os
import requests
from time import time
from cryptography.hazmat.primitives.asymmetric import ed25519
from dotenv import load_dotenv, find_dotenv
import keyboard  # 用于读取箭头键


class SpotTrader:


    def __init__(self):
        null = None
    # === 初始化环境变量和密钥 ===
    load_dotenv(find_dotenv())
    public_key = os.getenv("PUBLIC_KEY")
    secret_key = os.getenv("SECRET_KEY")
    private_key = ed25519.Ed25519PrivateKey.from_private_bytes(
        base64.b64decode(secret_key)
    )
    TOTAL_BALANCE = os.getenv("TOTAL_SUPPLY")
    TOKEN_NAME = os.getenv("TOKEN")

    # === API 接口 ===
    SYMBOL = f"{TOKEN_NAME}_USDC"
    QUOTE_ASSET = "USDC"
    DEFAULT_45 = 0.45
    DEFAULT_90 = 0.90
    PRICE_URL = f"https://api.backpack.exchange/api/v1/ticker?symbol={SYMBOL}"
    BALANCE_URL = "https://api.backpack.exchange/api/v1/capital"
    ORDER_URL = "https://api.backpack.exchange/api/v1/order"
    TOKEN_SUPPLY="0"
    side=""
    ISCONNECTED = False
    ratio=0.00

    # === 获取最新价格 ===
    def get_price(self):
        resp = requests.get(self.PRICE_URL)
        try:
            data = resp.json()
            print("API 返回数据:", data)  
            return float(data["lastPrice"])  # 再尝试取价格
        except Exception as e:
            print("解析价格失败:", e)
            print("原始响应文本:", resp.text)
            raise

    def change_connect(self):
        
        self.ISCONNECTED = True

    def change_ratio(self,ra):       
        self.ratio = ra

    # === 获取当前 USDC 余额 ===


    def get_uscd_balance(self):
        timestamp = int(time() * 1000)
        window = "5000"
        instruction = "balanceQuery"

        sign_str = f"instruction={instruction}&timestamp={timestamp}&window={window}"
        signature = base64.b64encode(self.private_key.sign(sign_str.encode())).decode()
        headers = {
            "X-API-Key": self.public_key,
            "X-Signature": signature,
            "X-Timestamp": str(timestamp),
            "X-Window": window,
        }

        resp = requests.get(self.BALANCE_URL, headers=headers)
        if resp.status_code != 200:
            print(f"请求资产接口失败，状态码: {resp.status_code}, 内容: {resp.text}")
            return 0.0
        balances = resp.json().get("assets", [])

        data = resp.json()
        print("账户资产信息:", data)
        balances = float(data["USDC"]["available"])
        
        if(self.side=="Ask"):
            self.TOKEN_SUPPLY = float(data[self.TOKEN_NAME]["available"])
            print(f"当前 {self.TOKEN_NAME} 可用余额: {self.TOKEN_SUPPLY}")
    


        return float(f"{balances:.2f}")

    # === 构造签名 ===
    def create_signature(self,instruction: str, params: dict, timestamp: int, window: str):
        sign_str = f"instruction={instruction}"
        sorted_params = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
        if sorted_params:
            sign_str += f"&{sorted_params}"
        sign_str += f"&timestamp={timestamp}&window={window}"
        signature = self.private_key.sign(sign_str.encode())
        return base64.b64encode(signature).decode()

    # === 监听 ↑↓ 和 杠杆输入 ===
    def listen_trade_direction(self):
        print("请按 ↑ 表示开多，↓ 表示开空")
        while True:
            if keyboard.is_pressed("up"):
                print("检测到 ↑：开多 (Bid)")
                self.side="Bid"
                return "Bid"
            elif keyboard.is_pressed("down"):
                print("检测到 ↓：开空 (Ask)")
                self.side="Ask"
                return "Ask"
            
    def listen_trade_direction1(self,bid):
        try:
            if bid not in ["Ask", "Bid"]:
                raise ValueError("self.side not valid")  # 主动抛出异常
            self.side = bid
            print(f"当前方向设置为: {self.side}")
        except Exception as e:
            print("输入错误，请重新输入：", e)
    # === 主函数 ===
    def main(self):
        print(self.ISCONNECTED)
        uscd_balance = self.TOTAL_BALANCE

        if not self.ISCONNECTED:

            self.side = self.listen_trade_direction()


            multiplier_input = input("请输入杠杆倍数 (0=45%, 1=90%, 其他=倍数)：")
            if multiplier_input == "0":
                self.ratio = self.DEFAULT_45
            elif multiplier_input == "1":
                self.ratio = self.DEFAULT_90
            else:
                try:
                    self.ratio = float(multiplier_input)
                except ValueError:
                    print("输入错误，默认使用 45%")
                    self.ratio = float(self.DEFAULT_45)
                print(f"杠杆倍数: {self.ratio}")
            

        current_price = self.get_price()
        print(f"当{self.TOKEN_NAME}/USDC 价格: {current_price}")
        print(f"当前 USDC 可用余额: {uscd_balance}")

        # 下单数量 = (USDC * 杠杆倍数) / 当前价格
        base_quantity = float(self.TOTAL_BALANCE) * self.ratio / current_price
        print(f"下单 {self.TOKEN_NAME} 数量: {base_quantity:.3f}")

        if base_quantity < 0.01:
            print("下单数量过小，请检查账户余额和杠杆倍数")
            return

        # 构造订单
        order_params = {
            "symbol": self.SYMBOL,
            "side": self.side,
            "orderType": "Limit",
            "price": f"{current_price:.2f}",
            "quantity": f"{base_quantity:.2f}",
            "timeInForce": "GTC",
            "clientId": int(time()),
            "selfTradePrevention": "RejectTaker"
        }

        # 发单
        timestamp = int(time() * 1000)
        window = "5000"
        signature = self.create_signature("orderExecute", order_params, timestamp, window)

        headers = {
            "X-API-Key": self.public_key,
            "X-Signature": signature,
            "X-Timestamp": str(timestamp),
            "X-Window": window,
            "Content-Type": "application/json; charset=utf-8",
        }



        response = requests.post(self.ORDER_URL, headers=headers, json=order_params)
        print("响应状态码:", response.status_code)
        try:
            print("响应 JSON:", response.json())
        except Exception:
            print("响应文本:", response.text)

    if __name__ == "__main__":
        main()

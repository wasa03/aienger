def calculator():
    """簡単な計算機プログラム"""
    print("=== 簡単な計算機 ===")
    
    try:
        # 1つ目の数値を入力
        num1 = float(input("1つ目の数値を入力してください: "))
        
        # 演算子を入力
        operator = input("演算子を入力してください (+, -, *, /): ")
        
        # 2つ目の数値を入力
        num2 = float(input("2つ目の数値を入力してください: "))
        
        # 演算子に応じて計算
        if operator == '+':
            result = num1 + num2
        elif operator == '-':
            result = num1 - num2
        elif operator == '*':
            result = num1 * num2
        elif operator == '/':
            if num2 == 0:
                print("エラー: 0で割ることはできません。")
                return
            result = num1 / num2
        else:
            print(f"エラー: '{operator}' は無効な演算子です。")
            print("使用可能な演算子: +, -, *, /")
            return
        
        # 結果を表示
        print(f"\n結果: {num1} {operator} {num2} = {result}")
        
    except ValueError:
        print("エラー: 数値を入力してください。")
    except Exception as e:
        print(f"エラーが発生しました: {e}")

if __name__ == "__main__":
    calculator()


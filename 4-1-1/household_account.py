def household_account():
    """家計簿アプリ - 1日の支出を記録して合計を表示"""
    print("=== 家計簿アプリ ===")
    print("支出を記録します。終了するには「終了」または「exit」と入力してください。\n")
    
    expenses = []  # 支出のリスト [(項目, 金額), ...]
    
    while True:
        try:
            # 項目名を入力
            item = input("使った項目を入力してください（終了する場合は「終了」または「exit」）: ").strip()
            
            # 終了チェック
            if item.lower() in ['終了', 'exit']:
                break
            
            if not item:
                print("項目名を入力してください。\n")
                continue
            
            # 金額を入力
            amount_str = input("金額を入力してください: ").strip()
            
            try:
                amount = float(amount_str)
                if amount < 0:
                    print("金額は0以上を入力してください。\n")
                    continue
                
                # 支出を記録
                expenses.append((item, amount))
                print(f"記録しました: {item} - {amount:,.0f}円\n")
                
            except ValueError:
                print("有効な数値を入力してください。\n")
                continue
                
        except KeyboardInterrupt:
            print("\n\n中断されました。")
            break
        except Exception as e:
            print(f"エラーが発生しました: {e}\n")
            continue
    
    # 合計金額を計算して表示
    print("\n" + "="*40)
    print("【1日の支出合計】")
    print("="*40)
    
    if expenses:
        total = 0
        for item, amount in expenses:
            print(f"  {item}: {amount:,.0f}円")
            total += amount
        
        print("-"*40)
        print(f"合計: {total:,.0f}円")
    else:
        print("  記録された支出はありません。")
    
    print("="*40)

if __name__ == "__main__":
    household_account()


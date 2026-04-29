```python
def generate_pro_con_list(decision_topic):
    """
    Generates a simple pro and con list for a given decision.
    """
    print(f"\n--- DECISION: {decision_topic.upper()} ---")
    
    pros = []
    cons = []

    print("\n--- PROS ---")
    while True:
        pro = input("Add a pro (or type 'done'): ")
        if pro.lower() == 'done':
            break
        pros.append(pro)

    print("\n--- CONS ---")
    while True:
        con = input("Add a con (or type 'done'): ")
        if con.lower() == 'done':
            break
        cons.append(con)

    print(f"\n--- SUMMARY FOR: {decision_topic.upper()} ---")
    print("Pros:")
    if pros:
        for i, p in enumerate(pros, 1):
            print(f"  {i}. {p}")
    else:
        print("  No pros listed.")

    print("\nCons:")
    if cons:
        for i, c in enumerate(cons, 1):
            print(f"  {i}. {c}")
    else:
        print("  No cons listed.")

if __name__ == "__main__":
    decision = input("What decision are you trying to make? ")
    generate_pro_con_list(decision)
```
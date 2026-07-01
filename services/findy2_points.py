from datetime import date, datetime, timedelta


POINT_POLICY = {
    "signup": {"amount": 500, "dailyLimit": 1, "minLength": 0},
    "post": {"amount": 20, "dailyLimit": 5, "minLength": 8},
    "comment": {"amount": 5, "dailyLimit": 20, "minLength": 5},
    "event": {"amount": 100, "dailyLimit": 10, "minLength": 0},
    "report_reward": {"amount": 20, "dailyLimit": 5, "minLength": 0},
    "admin": {"amount": 0, "dailyLimit": 999, "minLength": 0},
}


def _today():
    return date.today().isoformat()


def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def _expires_at(months=12):
    return (datetime.now() + timedelta(days=365 if months == 12 else months * 30)).strftime("%Y-%m-%d")


def create_point_wallet(userId):
    return {
        "userId": userId,
        "balance": 0,
        "totalEarned": 0,
        "totalUsed": 0,
        "updatedAt": _now(),
    }


def ensure_point_state(state, userId):
    wallets = state.setdefault("point_wallets", {})
    transactions = state.setdefault("point_transactions", [])
    if userId not in wallets:
        wallets[userId] = create_point_wallet(userId)
    return wallets[userId], transactions


def _same_day(transaction):
    return str(transaction.get("createdAt", "")).startswith(_today())


def _already_rewarded(transactions, userId, sourceType, relatedPostId=None):
    for transaction in transactions:
        if transaction.get("userId") != userId or transaction.get("sourceType") != sourceType:
            continue
        if relatedPostId is None:
            return True
        if transaction.get("relatedPostId") == relatedPostId:
            return True
    return False


def _daily_count(transactions, userId, sourceType):
    return sum(
        1
        for transaction in transactions
        if transaction.get("userId") == userId
        and transaction.get("sourceType") == sourceType
        and transaction.get("type") == "earn"
        and transaction.get("status") == "confirmed"
        and _same_day(transaction)
    )


def create_point_transaction(
    userId,
    type,
    amount,
    reason,
    sourceType,
    relatedPostId=None,
    status="confirmed",
):
    return {
        "id": f"point_{sourceType}_{int(datetime.now().timestamp() * 1000)}",
        "userId": userId,
        "type": type,
        "amount": int(amount),
        "reason": reason,
        "sourceType": sourceType,
        "relatedPostId": relatedPostId,
        "createdAt": _now(),
        "expiresAt": _expires_at() if type == "earn" else "",
        "status": status,
    }


def earn_points(state, userId, sourceType, reason="", amount=None, relatedPostId=None, text=""):
    if not userId:
        return None
    policy = POINT_POLICY.get(sourceType, {"amount": 0, "dailyLimit": 999, "minLength": 0})
    reward_amount = int(amount if amount is not None else policy.get("amount", 0))
    if reward_amount <= 0:
        return None
    if len((text or "").strip()) < int(policy.get("minLength", 0)):
        return None
    wallet, transactions = ensure_point_state(state, userId)
    if sourceType == "signup" and _already_rewarded(transactions, userId, "signup"):
        return None
    if relatedPostId and _already_rewarded(transactions, userId, sourceType, relatedPostId):
        return None
    if _daily_count(transactions, userId, sourceType) >= int(policy.get("dailyLimit", 999)):
        return None
    transaction = create_point_transaction(
        userId,
        "earn",
        reward_amount,
        reason or "FINDY 활동 보상",
        sourceType,
        relatedPostId=relatedPostId,
    )
    transactions.append(transaction)
    wallet["balance"] = int(wallet.get("balance", 0)) + reward_amount
    wallet["totalEarned"] = int(wallet.get("totalEarned", 0)) + reward_amount
    wallet["updatedAt"] = _now()
    return transaction


def use_points(state, userId, amount, reason="", sourceType="event", relatedPostId=None):
    if not userId:
        return None
    wallet, transactions = ensure_point_state(state, userId)
    amount = int(amount)
    if amount <= 0 or int(wallet.get("balance", 0)) < amount:
        return None
    transaction = create_point_transaction(
        userId,
        "use",
        amount,
        reason or "FINDY 포인트 사용",
        sourceType,
        relatedPostId=relatedPostId,
    )
    transactions.append(transaction)
    wallet["balance"] = int(wallet.get("balance", 0)) - amount
    wallet["totalUsed"] = int(wallet.get("totalUsed", 0)) + amount
    wallet["updatedAt"] = _now()
    return transaction


def revoke_points(state, userId, amount, reason="", relatedPostId=None):
    if not userId:
        return None
    wallet, transactions = ensure_point_state(state, userId)
    amount = min(int(amount), int(wallet.get("balance", 0)))
    if amount <= 0:
        return None
    transaction = create_point_transaction(
        userId,
        "revoke",
        amount,
        reason or "부정 또는 삭제 콘텐츠 보상 회수",
        "admin",
        relatedPostId=relatedPostId,
    )
    transactions.append(transaction)
    wallet["balance"] = int(wallet.get("balance", 0)) - amount
    wallet["updatedAt"] = _now()
    return transaction


def point_summary(state, userId):
    wallet, transactions = ensure_point_state(state, userId)
    return {
        "wallet": wallet,
        "recentTransactions": [
            transaction
            for transaction in reversed(transactions)
            if transaction.get("userId") == userId
        ][:10],
    }

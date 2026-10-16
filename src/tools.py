import ast
import operator
from config import WORKSPACE
from src.rag import search_documents
from src.providers import jev_preferences

OPS={ast.Add:operator.add,ast.Sub:operator.sub,ast.Mult:operator.mul,ast.Div:operator.truediv,
     ast.FloorDiv:operator.floordiv,ast.Mod:operator.mod,ast.Pow:operator.pow,
     ast.UAdd:operator.pos,ast.USub:operator.neg}

def _eval(node):
    if isinstance(node,ast.Constant) and type(node.value) in (int,float):
        if abs(node.value)>1e12: raise ValueError('数値が大きすぎます')
        return node.value
    if isinstance(node,ast.UnaryOp) and type(node.op) in OPS:
        return OPS[type(node.op)](_eval(node.operand))
    if isinstance(node,ast.BinOp) and type(node.op) in OPS:
        a,b=_eval(node.left),_eval(node.right)
        if isinstance(node.op,ast.Pow) and (abs(b)>8 or abs(a)>1e6): raise ValueError('指数演算が大きすぎます')
        result=OPS[type(node.op)](a,b)
        if abs(result)>1e15: raise ValueError('結果が大きすぎます')
        return result
    raise ValueError('許可されない式です')

def calculate(expression):
    if len(expression)>120: raise ValueError('式が長すぎます')
    return str(_eval(ast.parse(expression,mode='eval').body))

def list_workspace_files():
    return '\n'.join(p.name for p in sorted(WORKSPACE.iterdir()) if p.is_file()) or 'ファイルなし'

def read_workspace_file(filename):
    path=(WORKSPACE / filename).resolve()
    if path.parent != WORKSPACE.resolve() or path.suffix.lower() not in {'.txt','.md','.csv'}:
        raise ValueError('workspace直下のTXT/MD/CSVのみ読めます')
    if path.stat().st_size>200_000: raise ValueError('ファイルが大きすぎます')
    return path.read_text(encoding='utf-8-sig')[:20000]

def search_knowledge_base(query):
    results = search_documents(query)
    if not results:
        return '一致する文書なし'

    # Jev receives only the user's query and short retrieved passages, and only after
    # explicit, independently persisted Jev consent. It receives no tools or credentials.
    enabled, consented = jev_preferences()
    if enabled and consented:
        try:
            from src.jev import relevance_probability
            import os
            threshold = float(os.getenv("JEV_RELEVANCE_THRESHOLD", "0.80"))
            threshold = max(0.0, min(1.0, threshold))
            judged = []
            for item in results[:4]:
                probability = relevance_probability(query, item.get('source', ''), item.get('content', ''))
                if probability >= threshold:
                    judged.append(item)
            # If all candidates are rejected, do not silently claim that no evidence exists;
            # preserve local search results and label the fallback.
            if judged:
                results = judged
            else:
                return ('Jevがしきい値以上の関連文書を選べなかったため、ローカル検索結果を表示します。\n\n'
                        + '\n\n'.join(f"出典: {x['source']}\n{x['content']}" for x in results))
        except Exception as exc:
            # Availability failure must not block the existing local knowledge search.
            return (f'Jev判定を利用できなかったため、ローカル検索結果を表示します（{type(exc).__name__}）。\n\n'
                    + '\n\n'.join(f"出典: {x['source']}\n{x['content']}" for x in results))
    return '\n\n'.join(f"出典: {x['source']}\n{x['content']}" for x in results) or '一致する文書なし'

FUNCTIONS={
 'calculate':calculate,
 'list_workspace_files':list_workspace_files,
 'read_workspace_file':read_workspace_file,
 'search_knowledge_base':search_knowledge_base,
}
SCHEMAS=[
 {'type':'function','function':{'name':'calculate','description':'安全な算術式を計算する','parameters':{'type':'object','properties':{'expression':{'type':'string'}},'required':['expression']}}},
 {'type':'function','function':{'name':'list_workspace_files','description':'作業フォルダ内のファイル一覧を返す','parameters':{'type':'object','properties':{}}}},
 {'type':'function','function':{'name':'read_workspace_file','description':'作業フォルダ直下のテキストファイルを読む','parameters':{'type':'object','properties':{'filename':{'type':'string'}},'required':['filename']}}},
 {'type':'function','function':{'name':'search_knowledge_base','description':'登録文書を全文検索する','parameters':{'type':'object','properties':{'query':{'type':'string'}},'required':['query']}}},
]

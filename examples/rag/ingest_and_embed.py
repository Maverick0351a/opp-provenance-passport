from opp.decorators import stamp
from odin_sdk.client import OPEClient
import os

GW = os.getenv("OPP_GATEWAY_URL", "http://127.0.0.1:8080")
SEED = os.getenv("ODIN_SENDER_PRIV_B64")
KID = os.getenv("ODIN_SENDER_KID", "opp-demo")

client = OPEClient(gateway_url=GW, sender_priv_b64=SEED, sender_kid=KID)

@stamp("ingest.v1", attrs={"source":"folder"}, client=client)
def ingest(paths):
    return [open(p,'r',encoding='utf-8').read() for p in paths]

@stamp("embed.v1", attrs={"model":"mini-emb"} , client=client)
def embed(docs):
    return [len(d) for d in docs]  # dummy

@stamp("index.v1", attrs={"engine":"toy"}, client=client)
def build_index(vectors):
    return {"avg": sum(vectors)/max(1,len(vectors))}

if __name__ == "__main__":
    docs = ingest(["README.md"])
    vecs = embed(docs)
    idx = build_index(vecs)
    print("Index:", idx)

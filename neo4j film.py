# -*- coding: utf-8 -*-
from neo4j import GraphDatabase
import json
import os
print(os.getcwd())


# NEO4J BAĞLANTI AYARLARI

URI = "bolt://localhost:7687"
USERNAME = "neo4j"
PASSWORD = "Lene.Nisa"

driver = None
selected_movie = None
last_search_results = []

# BAĞLANTI

def connect():
    global driver
    try:
        driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))
        with driver.session() as session:
            session.run("RETURN 1")
        return True
    except:
        return False


# FİLM ARAMA

def search_movie():
    global last_search_results

    keyword = input("Aranacak film adı: ").strip()

    if not keyword:
        print("Boş arama yapılamaz.")
        return

    query = """
    MATCH (m:Movie)
    WHERE toLower(m.title) CONTAINS toLower($key)
    RETURN m.title AS title, m.released AS year
    ORDER BY year
    """

    with driver.session() as session:
        result = session.run(query, key=keyword)
        last_search_results = result.data()

    if not last_search_results:
        print("Sonuç bulunamadı.")
        return

    for i, movie in enumerate(last_search_results, 1):
        print(f"{i}) {movie['title']} ({movie['year']})")



# FİLM DETAY

def show_movie_details():
    global selected_movie

    if not last_search_results:
        print("Önce film arayın.")
        return

    while True:
        try:
            secim = int(input("Film numarası seçiniz: "))
            if 1 <= secim <= len(last_search_results):
                selected_movie = last_search_results[secim - 1]["title"]
                break
            else:
                print("Geçersiz numara.")
        except:
            print("Sayı giriniz.")

    query = """
    MATCH (m:Movie {title:$title})
    OPTIONAL MATCH (p:Person)-[:DIRECTED]->(m)
    OPTIONAL MATCH (a:Person)-[:ACTED_IN]->(m)
    RETURN m.title AS title,
           m.released AS year,
           m.tagline AS tagline,
           collect(DISTINCT p.name) AS directors,
           collect(DISTINCT a.name)[0..5] AS actors
    """

    with driver.session() as session:
        record = session.run(query, title=selected_movie).single()

    if not record:
        print("Film detayı bulunamadı.")
        return

    print("\n Film Bilgileri")
    print("Ad:", record["title"])
    print("Yıl:", record["year"])
    print("Tagline:", record["tagline"] if record["tagline"] else "Yok")

    print("\n Yönetmen(ler):")
    for d in record["directors"]:
        print("-", d)

    print("\n Oyuncular:")
    for a in record["actors"]:
        print("-", a)

# GRAPH.JSON OLUŞTURMA

def export_graph():
    if not selected_movie:
        print("Önce film seçmelisiniz.")
        return

    query = """
    MATCH (m:Movie {title:$title})<- [r]-(p:Person)
    RETURN m, p, type(r) AS rel
    """

    nodes = {}
    links = []

    with driver.session() as session:
        result = session.run(query, title=selected_movie)

        for record in result:
            movie = record["m"]
            person = record["p"]
            rel = record["rel"]

            nodes[movie.id] = {"id": movie.id, "label": "Movie", "title": movie["title"]}
            nodes[person.id] = {"id": person.id, "label": "Person", "name": person["name"]}

            links.append({
                "source": person.id,
                "target": movie.id,
                "type": rel
            })

    graph = {
        "nodes": list(nodes.values()),
        "links": links
    }

    os.makedirs("exports", exist_ok=True)
    with open("exports/graph.json", "w", encoding="utf-8") as f:
        json.dump(graph, f, indent=2, ensure_ascii=False)

    print("graph.json oluşturuldu: exports/graph.json")


# ANA MENÜ

def menu():
    while True:
        print("\n--- MovieGraphPy ---")
        print("1) Film Ara")
        print("2) Film Detayı Göster")
        print("3) Seçili Film için graph.json Oluştur")
        print("4) Çıkış")

        secim = input("Seçiminiz: ")

        if secim == "1":
            search_movie()
        elif secim == "2":
            show_movie_details()
        elif secim == "3":
            export_graph()
        elif secim == "4":
            print("Çıkılıyor...")
            break
        else:
            print("Geçersiz seçim.")

# PROGRAM BAŞLANGICI

if __name__ == "__main__":
    if connect():
        menu()
    else:
        print("Neo4j bağlantısı kurulamadı.")
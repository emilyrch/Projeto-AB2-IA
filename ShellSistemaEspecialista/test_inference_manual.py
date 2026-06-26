from src.explanation_engine import ExplanationEngine
from src.inference_engine import InferenceEngine
from src.knowledge_base import KnowledgeBase


def check(name, condition, details=""):
    status = "PASS" if condition else "FAIL"
    print(f"{status} - {name}")
    if details and not condition:
        print(f"  {details}")
    return condition


def main():
    kb = KnowledgeBase.load("data/knowledge_base.json")
    engine = InferenceEngine(kb)
    explanations = ExplanationEngine(kb)
    passed = []

    partial_power = engine.forward_chain({"computador_desliga_sozinho": "sim"})
    passed.append(
        check(
            "Caso 1: desligamento sozinho gera regras avaliadas e compatibilidade parcial",
            not partial_power.fired_rules
            and partial_power.evaluated_rules
            and any(rule["status"] == "inconclusiva" for rule in partial_power.evaluated_rules)
            and any(value > 0 for value in partial_power.compatibility.values())
            and partial_power.reasoning_path,
            str(partial_power.to_dict()),
        )
    )

    confirmed_power = engine.forward_chain({"computador_desliga_sozinho": "sim", "cheiro_queimado": "sim"})
    passed.append(
        check(
            "Caso 2: fonte confirmada por desligamento e cheiro de queimado",
            confirmed_power.final_diagnosis
            and confirmed_power.final_diagnosis["id"] == "problema_fonte"
            and any(rule["id"] == "R12" for rule in confirmed_power.fired_rules)
            and confirmed_power.compatibility.get("problema_fonte") == 100.0
            and confirmed_power.recommendations,
            str(confirmed_power.to_dict()),
        )
    )

    slow_only = engine.forward_chain({"computador_lento": "sim"})
    passed.append(
        check(
            "Caso 3: computador lento isolado nao confirma diagnostico, mas avalia regras relacionadas",
            slow_only.final_diagnosis is None
            and slow_only.evaluated_rules
            and any("computador_lento = sim" in rule["condicoes_satisfeitas"] for rule in slow_only.evaluated_rules)
            and any(value > 0 for value in slow_only.compatibility.values()),
            str(slow_only.to_dict()),
        )
    )

    malware = engine.forward_chain({"popups_estranhos": "sim", "navegador_redirecionando": "sim"})
    how = explanations.explain_how_conclusion(malware)
    passed.append(
        check(
            "Caso 4: malware confirmado com regra, recomendacao e explicacao como",
            malware.final_diagnosis
            and malware.final_diagnosis["id"] == "malware"
            and any(rule["id"] == "R09" for rule in malware.fired_rules)
            and malware.recommendations
            and "R09" in how
            and "popups_estranhos" in how
            and "navegador_redirecionando" in how,
            f"result={malware.to_dict()} how={how}",
        )
    )

    ram_false = engine.backward_chain({"tela_azul": "sim", "reinicia_frequentemente": "nao"}, "falha_memoria_ram")
    r03 = next((rule for rule in ram_false.evaluated_rules if rule["id"] == "R03"), None)
    passed.append(
        check(
            "Regressao: RAM nao confirmada com uma condicao falsa",
            ram_false.final_diagnosis is None and r03 and r03["status"] == "falhou" and not ram_false.recommendations,
            str(ram_false.to_dict()),
        )
    )

    ram_true = engine.backward_chain({"tela_azul": "sim", "reinicia_frequentemente": "sim"}, "falha_memoria_ram")
    passed.append(
        check(
            "Regressao: RAM confirmada com R03 satisfeita",
            ram_true.final_diagnosis
            and ram_true.final_diagnosis["id"] == "falha_memoria_ram"
            and any(rule["id"] == "R03" for rule in ram_true.fired_rules)
            and ram_true.recommendations,
            str(ram_true.to_dict()),
        )
    )

    disk = engine.forward_chain({"computador_lento": "sim", "disco_100_porcento": "sim"})
    passed.append(
        check(
            "Regressao: lentidao e disco 100 confirma HD/SSD",
            disk.final_diagnosis and disk.final_diagnosis["id"] == "problema_hd_ssd",
            str(disk.to_dict()),
        )
    )

    hybrid_malware = engine.hybrid_chain({"popups_estranhos": "sim", "navegador_redirecionando": "sim"}, "malware")
    passed.append(
        check(
            "Regressao: hibrido confirma malware",
            hybrid_malware.final_diagnosis and hybrid_malware.final_diagnosis["id"] == "malware",
            str(hybrid_malware.to_dict()),
        )
    )

    if not all(passed):
        raise SystemExit(1)
    print("Todos os testes manuais passaram.")


if __name__ == "__main__":
    main()

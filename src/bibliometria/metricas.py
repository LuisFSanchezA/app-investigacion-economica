"""Métricas bibliométricas calculadas sobre un corpus de trabajos.

Todas las funciones reciben un DataFrame con al menos las columnas:
- titulo, anio, autores, instituciones, paises, fuente, citas, tipo, conceptos

Devuelven estructuras simples (dicts, listas, DataFrames) listas para graficar.
"""

from __future__ import annotations

import re
from collections import Counter

import pandas as pd


# ---------------------------------------------------------------------------
# Utilidades internas
# ---------------------------------------------------------------------------

def _separar_lista(valor: str | None) -> list[str]:
    """Separa un string con '; ' en lista de strings limpios."""
    if not valor or not isinstance(valor, str):
        return []
    return [x.strip() for x in valor.split(";") if x.strip()]


def _validar_columnas(df: pd.DataFrame, requeridas: list[str]) -> None:
    """Lanza ValueError si faltan columnas."""
    faltantes = [c for c in requeridas if c not in df.columns]
    if faltantes:
        raise ValueError(f"Faltan columnas en el corpus: {faltantes}")


# ---------------------------------------------------------------------------
# Métricas generales
# ---------------------------------------------------------------------------

def resumen_general(df: pd.DataFrame) -> dict:
    """Devuelve métricas generales del corpus.

    Devuelve
    -------
    dict con:
        - n_trabajos
        - anio_min, anio_max
        - citas_total, citas_media, citas_mediana
        - h_index
        - pct_open_access
        - n_autores_unicos
        - n_fuentes_unicas
        - tipos (dict tipo -> count)
    """
    if df.empty:
        raise ValueError("El corpus está vacío.")

    _validar_columnas(df, ["titulo", "anio", "citas"])

    anios = pd.to_numeric(df["anio"], errors="coerce").dropna()
    citas = pd.to_numeric(df["citas"], errors="coerce").fillna(0)

    # h-index: nº de trabajos con al menos h citas
    citas_ordenadas = sorted(citas, reverse=True)
    h_index = 0
    for i, c in enumerate(citas_ordenadas, start=1):
        if c >= i:
            h_index = i
        else:
            break

    # Autores únicos
    autores_set = set()
    for v in df.get("autores", pd.Series(dtype=str)).fillna(""):
        autores_set.update(_separar_lista(v))

    # Fuentes únicas
    fuentes_set = set()
    for v in df.get("fuente", pd.Series(dtype=str)).fillna(""):
        if v.strip():
            fuentes_set.add(v.strip())

    # Tipos
    tipos = df.get("tipo", pd.Series(dtype=str)).fillna("desconocido").value_counts().to_dict()

    # Open access
    if "open_access" in df.columns:
        pct_oa = float(df["open_access"].fillna(False).astype(bool).mean() * 100)
    else:
        pct_oa = 0.0

    return {
        "n_trabajos": len(df),
        "anio_min": int(anios.min()) if not anios.empty else None,
        "anio_max": int(anios.max()) if not anios.empty else None,
        "citas_total": int(citas.sum()),
        "citas_media": float(citas.mean()),
        "citas_mediana": float(citas.median()),
        "h_index": h_index,
        "pct_open_access": round(pct_oa, 1),
        "n_autores_unicos": len(autores_set),
        "n_fuentes_unicas": len(fuentes_set),
        "tipos": tipos,
    }


# ---------------------------------------------------------------------------
# Producción por año
# ---------------------------------------------------------------------------

def produccion_por_anio(df: pd.DataFrame) -> pd.DataFrame:
    """Devuelve DataFrame con columnas: anio, n_trabajos, citas_total."""
    _validar_columnas(df, ["anio"])
    if df.empty:
        return pd.DataFrame(columns=["anio", "n_trabajos", "citas_total"])

    df2 = df.copy()
    df2["anio"] = pd.to_numeric(df2["anio"], errors="coerce")
    df2 = df2.dropna(subset=["anio"])
    df2["anio"] = df2["anio"].astype(int)
    df2["citas"] = pd.to_numeric(df2.get("citas", 0), errors="coerce").fillna(0)

    return (
        df2.groupby("anio")
        .agg(n_trabajos=("titulo", "count"), citas_total=("citas", "sum"))
        .reset_index()
        .sort_values("anio")
    )


# ---------------------------------------------------------------------------
# Top N por campo (autores, instituciones, paises, fuentes, conceptos)
# ---------------------------------------------------------------------------

def top_autores(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """Top N autores por número de trabajos. Columnas: autor, n_trabajos, citas_total."""
    _validar_columnas(df, ["autores"])
    contador: Counter = Counter()
    citas_por_autor: dict[str, float] = {}
    for _, row in df.iterrows():
        citas = float(row.get("citas", 0) or 0)
        for autor in set(_separar_lista(row.get("autores", ""))):
            contador[autor] += 1
            citas_por_autor[autor] = citas_por_autor.get(autor, 0) + citas
        # Orden determinista: por nº trabajos (desc), luego citas (desc),
    # luego nombre (asc) para desempatar.
    items = sorted(
        contador.items(),
        key=lambda kv: (-kv[1], -citas_por_autor.get(kv[0], 0), kv[0]),
    )[:n]
    filas = [
        {"autor": a, "n_trabajos": c, "citas_total": citas_por_autor.get(a, 0)}
        for a, c in items
    ]
    return pd.DataFrame(filas)

def top_instituciones(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """Top N instituciones por número de trabajos."""
    _validar_columnas(df, ["instituciones"])
    contador: Counter = Counter()
    for v in df["instituciones"].fillna(""):
        for inst in set(_separar_lista(v)):
            contador[inst] += 1
    filas = [{"institucion": k, "n_trabajos": v} for k, v in contador.most_common(n)]
    return pd.DataFrame(filas)


def top_paises(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """Top N países por número de trabajos."""
    _validar_columnas(df, ["paises"])
    contador: Counter = Counter()
    for v in df["paises"].fillna(""):
        for p in set(_separar_lista(v)):
            contador[p] += 1
    filas = [{"pais": k, "n_trabajos": v} for k, v in contador.most_common(n)]
    return pd.DataFrame(filas)


def top_fuentes(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """Top N fuentes (revistas, libros) por número de trabajos."""
    _validar_columnas(df, ["fuente"])
    contador: Counter = Counter()
    for v in df["fuente"].fillna(""):
        if v.strip():
            contador[v.strip()] += 1
    filas = [{"fuente": k, "n_trabajos": v} for k, v in contador.most_common(n)]
    return pd.DataFrame(filas)


def top_conceptos(df: pd.DataFrame, n: int = 20) -> pd.DataFrame:
    """Top N conceptos/palabras clave por frecuencia."""
    _validar_columnas(df, ["conceptos"])
    contador: Counter = Counter()
    for v in df["conceptos"].fillna(""):
        for c in set(_separar_lista(v)):
            contador[c] += 1
    filas = [{"concepto": k, "n_trabajos": v} for k, v in contador.most_common(n)]
    return pd.DataFrame(filas)


# ---------------------------------------------------------------------------
# Ley de Bradford (dispersión de la literatura por fuentes)
# ---------------------------------------------------------------------------

def ley_bradford(df: pd.DataFrame) -> pd.DataFrame:
    """Calcula la distribución de Bradford.

    Agrupa las fuentes en 3 zonas:
    - Zona 1: núcleo (pocas fuentes, muchos trabajos)
    - Zona 2: intermedias
    - Zona 3: periféricas (muchas fuentes, pocos trabajos)

    Devuelve DataFrame con: zona, n_fuentes, n_trabajos.
    """
    _validar_columnas(df, ["fuente"])
    fuentes = df["fuente"].fillna("").str.strip()
    fuentes = fuentes[fuentes != ""]
    if fuentes.empty:
        return pd.DataFrame(columns=["zona", "n_fuentes", "n_trabajos"])

    conteo = fuentes.value_counts().sort_values(ascending=False)
    total_trabajos = int(conteo.sum())

    if total_trabajos < 3:
        return pd.DataFrame(
            [{"zona": "Núcleo", "n_fuentes": len(conteo), "n_trabajos": total_trabajos}]
        )

    # Cortar en 3 zonas por tercios acumulados de trabajos
    acumulado = conteo.cumsum()
    tercio = total_trabajos / 3
    zonas = []
    zona_actual = 1
    n_fuentes_zona = 0
    n_trabajos_zona = 0
    for fuente, n in conteo.items():
        n_fuentes_zona += 1
        n_trabajos_zona += n
        if n_trabajos_zona >= tercio * zona_actual and zona_actual < 3:
            zonas.append(
                {"zona": f"Zona {zona_actual}", "n_fuentes": n_fuentes_zona, "n_trabajos": n_trabajos_zona}
            )
            zona_actual += 1
            n_fuentes_zona = 0
            n_trabajos_zona = 0
    if n_fuentes_zona > 0:
        zonas.append(
            {"zona": f"Zona {zona_actual}", "n_fuentes": n_fuentes_zona, "n_trabajos": n_trabajos_zona}
        )

    return pd.DataFrame(zonas)


# ---------------------------------------------------------------------------
# Ley de Lotka (productividad de autores)
# ---------------------------------------------------------------------------

def ley_lotka(df: pd.DataFrame) -> pd.DataFrame:
    """Calcula la distribución de Lotka.

    Agrupa autores por número de trabajos publicados.

    Devuelve DataFrame con: n_trabajos, n_autores, pct_autores.
    """
    _validar_columnas(df, ["autores"])
    contador: Counter = Counter()
    for v in df["autores"].fillna(""):
        for autor in set(_separar_lista(v)):
            contador[autor] += 1

    if not contador:
        return pd.DataFrame(columns=["n_trabajos", "n_autores", "pct_autores"])

    distribucion = Counter(contador.values())
    total_autores = sum(distribucion.values())
    filas = [
        {
            "n_trabajos": k,
            "n_autores": v,
            "pct_autores": round(v / total_autores * 100, 1),
        }
        for k, v in sorted(distribucion.items())
    ]
    return pd.DataFrame(filas)


# ---------------------------------------------------------------------------
# Distribución de citas
# ---------------------------------------------------------------------------

def distribucion_citas(df: pd.DataFrame) -> pd.DataFrame:
    """Devuelve DataFrame con: anio, citas (para histograma o scatter)."""
    _validar_columnas(df, ["anio", "citas"])
    df2 = df.copy()
    df2["anio"] = pd.to_numeric(df2["anio"], errors="coerce")
    df2["citas"] = pd.to_numeric(df2["citas"], errors="coerce").fillna(0)
    df2 = df2.dropna(subset=["anio"])
    return df2[["anio", "citas", "titulo"]].reset_index(drop=True)
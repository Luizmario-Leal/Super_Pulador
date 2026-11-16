import pygame
import sys

pygame.init()
LARGURA, ALTURA, TILE = 800, 480, 40
tela = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption("Super Pulador")
relogio = pygame.time.Clock()
fonte = pygame.font.SysFont("arial", 24)
fonte_grande = pygame.font.SysFont("arial", 52, bold=True)

# ---------- CONFIGURAÇÃO DA FASE (em colunas/linhas de 40px) ----------
COLUNAS = 90
BURACOS = [(18, 21), (40, 43), (62, 65)]                 # (coluna inicial, final)
PLATAFORMAS = [(8, 7, 3), (14, 6, 4), (24, 7, 3), (28, 5, 3), (33, 7, 4),
               (46, 7, 3), (50, 5, 3), (55, 7, 3), (68, 7, 4), (72, 5, 3)]  # (coluna, linha, tamanho)
INIMIGOS = [12, 30, 36, 48, 56, 70, 78]                  # colunas no chão
BANDEIRA = pygame.Rect(86 * TILE, 200, TILE, 200)
TEMPO_MAX, VIDAS = 100, 3


def desenhar_texto(msg, f, cor, x, y):
    img = f.render(msg, True, cor)
    tela.blit(img, img.get_rect(center=(x, y)))


def novo_jogo():
    solidos = [pygame.Rect(c * TILE, 10 * TILE, TILE, 2 * TILE) for c in range(COLUNAS)
               if not any(a <= c < b for a, b in BURACOS)]
    solidos += [pygame.Rect(c * TILE, r * TILE, n * TILE, TILE) for c, r, n in PLATAFORMAS]
    posicoes = [(c + i, r - 1) for c, r, n in PLATAFORMAS for i in range(n)]
    posicoes += [((a + b) // 2, 8) for a, b in BURACOS] + [(5, 9), (26, 9), (60, 9), (80, 9)]
    moedas = [pygame.Rect(c * TILE + 10, r * TILE + 10, 20, 20) for c, r in posicoes]
    inimigos = [{"r": pygame.Rect(c * TILE, 10 * TILE - 36, 36, 36), "d": 1,
                 "min": c * TILE - 100, "max": c * TILE + 100} for c in INIMIGOS]
    return {"solidos": solidos, "moedas": moedas, "inimigos": inimigos,
            "p": pygame.Rect(100, 10 * TILE - 40, 30, 40), "vy": 0, "chao": False,
            "vidas": VIDAS, "pontos": 0, "salvo": (100, 360), "invul": 0,
            "inicio": pygame.time.get_ticks()}


def mover(r, dx, dy, solidos):
    """Move o retângulo eixo por eixo e resolve colisões. Retorna (no_chao, bateu_y)."""
    chao = bateu_y = False
    r.x += dx
    for s in solidos:
        if r.colliderect(s):
            if dx > 0:
                r.right = s.left
            elif dx < 0:
                r.left = s.right
    r.y += round(dy)
    for s in solidos:
        if r.colliderect(s):
            bateu_y = True
            if dy > 0:
                r.bottom = s.top
                chao = True
            elif dy < 0:
                r.top = s.bottom
    return chao, bateu_y


def perder_vida(j):
    j["vidas"] -= 1
    j["p"].topleft = j["salvo"]
    j["vy"] = 0
    j["invul"] = 90


def atualizar(j):
    p, t = j["p"], pygame.key.get_pressed()
    dx = 5 * ((t[pygame.K_RIGHT] or t[pygame.K_d]) - (t[pygame.K_LEFT] or t[pygame.K_a]))
    pular = t[pygame.K_SPACE] or t[pygame.K_UP] or t[pygame.K_w]

    if pular and j["chao"]:
        j["vy"] = -15
    if not pular and j["vy"] < -5:      # soltar o botão = pulo mais curto
        j["vy"] = -5
    j["vy"] = min(j["vy"] + 0.8, 16)    # gravidade
    j["chao"], bateu_y = mover(p, dx, j["vy"], j["solidos"])
    if bateu_y:
        j["vy"] = 0
    p.left = max(p.left, 0)

    if p.top > ALTURA:                  # caiu no buraco
        perder_vida(j)
    if p.x > 1800 and j["salvo"][0] < 1800:
        j["salvo"] = (1800, 360)        # checkpoint
    j["invul"] = max(0, j["invul"] - 1)

    for m in j["moedas"][:]:
        if p.colliderect(m):
            j["moedas"].remove(m)
            j["pontos"] += 10

    for e in j["inimigos"][:]:
        r = e["r"]
        r.x += e["d"] * 2
        if r.x < e["min"] or r.x > e["max"]:
            e["d"] *= -1
        if p.colliderect(r):
            if j["vy"] > 0 and p.bottom - r.top < 20:   # pisou em cima
                j["inimigos"].remove(e)
                j["vy"] = -10
                j["pontos"] += 100
            elif j["invul"] == 0:
                perder_vida(j)

    restante = TEMPO_MAX - (pygame.time.get_ticks() - j["inicio"]) // 1000
    if p.colliderect(BANDEIRA):
        j["pontos"] += max(restante, 0) * 10            # bônus de tempo
        return "vitoria"
    if j["vidas"] <= 0 or restante <= 0:
        return "derrota"
    return "jogando"


def desenhar(j):
    p = j["p"]
    cam = max(0, min(p.centerx - LARGURA // 2, COLUNAS * TILE - LARGURA))
    tela.fill((107, 170, 255))

    for s in j["solidos"]:
        if s.right > cam and s.left < cam + LARGURA:
            r = s.move(-cam, 0)
            if s.height == TILE:        # plataforma de tijolo
                pygame.draw.rect(tela, (200, 80, 40), r)
                pygame.draw.rect(tela, (120, 40, 20), r, 3)
            else:                       # chão com grama
                pygame.draw.rect(tela, (150, 100, 50), r)
                pygame.draw.rect(tela, (60, 180, 60), (r.x, r.y, r.w, 8))

    for m in j["moedas"]:
        pygame.draw.circle(tela, (255, 220, 0), m.move(-cam, 0).center, 10)
    for e in j["inimigos"]:
        r = e["r"].move(-cam, 0)
        pygame.draw.rect(tela, (120, 60, 20), r, border_radius=8)
        pygame.draw.circle(tela, (255, 255, 255), (r.x + 10, r.y + 12), 5)
        pygame.draw.circle(tela, (255, 255, 255), (r.x + 26, r.y + 12), 5)

    b = BANDEIRA.move(-cam, 0)
    pygame.draw.rect(tela, (240, 240, 240), (b.x + 15, b.y, 8, b.h))
    pygame.draw.polygon(tela, (230, 50, 50), [(b.x + 23, b.y), (b.x + 63, b.y + 20), (b.x + 23, b.y + 40)])

    if j["invul"] % 10 < 5:             # pisca quando está invulnerável
        r = p.move(-cam, 0)
        pygame.draw.rect(tela, (40, 80, 220), r, border_radius=6)
        pygame.draw.rect(tela, (230, 40, 40), (r.x, r.y, r.w, 14), border_radius=6)

    restante = max(0, TEMPO_MAX - (pygame.time.get_ticks() - j["inicio"]) // 1000)
    desenhar_texto(f"Pontos: {j['pontos']}", fonte, (255, 255, 255), 90, 25)
    desenhar_texto(f"Vidas: {j['vidas']}", fonte, (255, 255, 255), LARGURA // 2, 25)
    desenhar_texto(f"Tempo: {restante}", fonte, (255, 255, 255), LARGURA - 90, 25)


def main():
    estado, jogo = "menu", novo_jogo()
    while True:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_RETURN and estado != "jogando":
                jogo, estado = novo_jogo(), "jogando"

        if estado == "jogando":
            estado = atualizar(jogo)
            desenhar(jogo)
        else:
            tela.fill((107, 170, 255))
            if estado == "menu":
                desenhar_texto("SUPER PULADOR", fonte_grande, (255, 255, 255), LARGURA // 2, 130)
                desenhar_texto("Setas/A/D movem  |  ESPAÇO pula", fonte, (20, 20, 80), LARGURA // 2, 230)
                desenhar_texto("Pise nos inimigos, pegue moedas e chegue à bandeira!", fonte, (20, 20, 80), LARGURA // 2, 270)
            elif estado == "vitoria":
                desenhar_texto("VOCÊ CHEGOU À BANDEIRA!", fonte_grande, (255, 255, 120), LARGURA // 2, 150)
                desenhar_texto(f"Pontos finais: {jogo['pontos']}", fonte, (20, 20, 80), LARGURA // 2, 250)
            else:
                desenhar_texto("GAME OVER", fonte_grande, (200, 30, 30), LARGURA // 2, 150)
                desenhar_texto(f"Pontos: {jogo['pontos']}", fonte, (20, 20, 80), LARGURA // 2, 250)
            desenhar_texto("Pressione ENTER para jogar", fonte, (255, 255, 255), LARGURA // 2, 370)

        pygame.display.flip()
        relogio.tick(60)


main()
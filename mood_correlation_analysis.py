"""
무드 Correlation 상세 분석
"""
import json
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# matplotlib 선택적 임포트
try:
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.use('Agg')  # GUI 없이 이미지 저장
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    print("⚠️  matplotlib 없음. 시각화는 생략됩니다.")

# API 테스트 결과 로드
with open('api_test_result.json', 'r', encoding='utf-8') as f:
    result = json.load(f)

print("=" * 80)
print("📊 무드 Correlation 상세 분석")
print("=" * 80)

# 배경 무드 정보
bg_mood = result['background_mood']
print(f"\n🎨 배경 무드:")
print(f"   스타일: {bg_mood['primary_style']}")
print(f"   카테고리: {bg_mood['category']}")
print(f"   따뜻함 점수: {bg_mood['warmth_score']:.3f}")
print(f"   주요 색상: {', '.join(bg_mood['dominant_colors'])}")

# 추천 상품 분석
products = result['recommended_products']
print(f"\n🛍️  추천 상품 {len(products)}개:")
print("=" * 80)

# 각 상품의 매칭 세부 정보
for idx, product in enumerate(products, 1):
    print(f"\n{idx}. {product['name'][:60]}")
    print(f"   가격: {product['price']:,}원")
    print(f"   전체 매칭 점수: {product['match_score']:.4f}")

    details = product['match_details']
    print(f"   세부 점수:")
    print(f"     - 색상 유사도 (Color):    {details['color_similarity']:.4f}")
    print(f"     - 물리적 유사도 (Physics): {details['physics_similarity']:.4f}")
    print(f"     - 스타일 유사도 (Style):   {details['style_similarity']:.4f}")

    # 각 요소의 기여도 계산 (weighted average 기반)
    # vector_manager.py의 가중치: color=0.3, physics=0.2, style=0.5
    color_contrib = details['color_similarity'] * 0.3
    physics_contrib = details['physics_similarity'] * 0.2
    style_contrib = details['style_similarity'] * 0.5

    print(f"   기여도 (가중치 적용):")
    print(f"     - 색상:   {color_contrib:.4f} (30%)")
    print(f"     - 물리적: {physics_contrib:.4f} (20%)")
    print(f"     - 스타일: {style_contrib:.4f} (50%)")
    print(f"     - 합계:   {color_contrib + physics_contrib + style_contrib:.4f}")

# 통계 분석
print("\n" + "=" * 80)
print("📈 통계 분석:")
print("=" * 80)

# 각 유사도 지표의 통계
color_scores = [p['match_details']['color_similarity'] for p in products]
physics_scores = [p['match_details']['physics_similarity'] for p in products]
style_scores = [p['match_details']['style_similarity'] for p in products]
total_scores = [p['match_score'] for p in products]

print(f"\n1. 색상 유사도 (Color Similarity)")
print(f"   평균: {np.mean(color_scores):.4f}")
print(f"   최고: {np.max(color_scores):.4f}")
print(f"   최저: {np.min(color_scores):.4f}")
print(f"   표준편차: {np.std(color_scores):.4f}")

print(f"\n2. 물리적 유사도 (Physics Similarity)")
print(f"   평균: {np.mean(physics_scores):.4f}")
print(f"   최고: {np.max(physics_scores):.4f}")
print(f"   최저: {np.min(physics_scores):.4f}")
print(f"   표준편차: {np.std(physics_scores):.4f}")

print(f"\n3. 스타일 유사도 (Style Similarity)")
print(f"   평균: {np.mean(style_scores):.4f}")
print(f"   최고: {np.max(style_scores):.4f}")
print(f"   최저: {np.min(style_scores):.4f}")
print(f"   표준편차: {np.std(style_scores):.4f}")

print(f"\n4. 전체 매칭 점수 (Total Match Score)")
print(f"   평균: {np.mean(total_scores):.4f}")
print(f"   최고: {np.max(total_scores):.4f}")
print(f"   최저: {np.min(total_scores):.4f}")
print(f"   표준편차: {np.std(total_scores):.4f}")

# 각 요소의 중요도 분석
print("\n" + "=" * 80)
print("🎯 매칭 요소 중요도 분석:")
print("=" * 80)

# 각 요소가 최종 점수에 미치는 영향
color_importance = np.corrcoef(color_scores, total_scores)[0, 1]
physics_importance = np.corrcoef(physics_scores, total_scores)[0, 1]
style_importance = np.corrcoef(style_scores, total_scores)[0, 1]

print(f"\n상관계수 (Correlation with Total Score):")
print(f"   색상:   {color_importance:.4f}")
print(f"   물리적: {physics_importance:.4f}")
print(f"   스타일: {style_importance:.4f}")

# 시각화
if HAS_MATPLOTLIB:
    print("\n📊 시각화 생성 중...")

    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    fig.suptitle('Mood Correlation Analysis', fontsize=16, fontweight='bold')

    # 1. 각 유사도 지표 비교 (막대 그래프)
    ax1 = axes[0, 0]
    x = np.arange(len(products))
    width = 0.25

    ax1.bar(x - width, color_scores, width, label='Color', alpha=0.8)
    ax1.bar(x, physics_scores, width, label='Physics', alpha=0.8)
    ax1.bar(x + width, style_scores, width, label='Style', alpha=0.8)

    ax1.set_ylabel('Similarity Score')
    ax1.set_xlabel('Product Index')
    ax1.set_title('Similarity Scores by Component')
    ax1.set_xticks(x)
    ax1.set_xticklabels([f'P{i+1}' for i in range(len(products))])
    ax1.legend()
    ax1.grid(axis='y', alpha=0.3)

    # 2. 전체 매칭 점수 (선 그래프)
    ax2 = axes[0, 1]
    ax2.plot(range(1, len(products)+1), total_scores, marker='o', linewidth=2, markersize=8)
    ax2.set_ylabel('Match Score')
    ax2.set_xlabel('Product Rank')
    ax2.set_title('Total Match Score by Rank')
    ax2.grid(True, alpha=0.3)
    ax2.set_xticks(range(1, len(products)+1))

    # 3. 각 요소의 평균 기여도 (파이 차트)
    ax3 = axes[1, 0]
    avg_color_contrib = np.mean([d['color_similarity'] for d in [p['match_details'] for p in products]]) * 0.3
    avg_physics_contrib = np.mean([d['physics_similarity'] for d in [p['match_details'] for p in products]]) * 0.2
    avg_style_contrib = np.mean([d['style_similarity'] for d in [p['match_details'] for p in products]]) * 0.5

    contributions = [avg_color_contrib, avg_physics_contrib, avg_style_contrib]
    labels = [f'Color\n({avg_color_contrib:.3f})',
              f'Physics\n({avg_physics_contrib:.3f})',
              f'Style\n({avg_style_contrib:.3f})']
    colors = ['#ff9999', '#66b3ff', '#99ff99']

    ax3.pie(contributions, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
    ax3.set_title('Average Contribution by Component')

    # 4. 산점도 (Style vs Color)
    ax4 = axes[1, 1]
    scatter = ax4.scatter(style_scores, color_scores,
                         c=total_scores, cmap='viridis',
                         s=200, alpha=0.6, edgecolors='black', linewidth=1.5)
    ax4.set_xlabel('Style Similarity')
    ax4.set_ylabel('Color Similarity')
    ax4.set_title('Style vs Color (colored by Total Score)')
    ax4.grid(True, alpha=0.3)

    # 색상 바 추가
    cbar = plt.colorbar(scatter, ax=ax4)
    cbar.set_label('Match Score')

    # 각 점에 순위 표시
    for i, (x, y) in enumerate(zip(style_scores, color_scores)):
        ax4.annotate(f'{i+1}', (x, y), fontsize=10, fontweight='bold',
                    ha='center', va='center')

    plt.tight_layout()
    plt.savefig('mood_correlation_analysis.png', dpi=300, bbox_inches='tight')
    print("✅ 시각화 저장: mood_correlation_analysis.png")
else:
    print("\n⚠️  matplotlib이 설치되지 않아 시각화를 생략합니다.")

# 결론
print("\n" + "=" * 80)
print("🎯 결론:")
print("=" * 80)

print(f"""
배경 무드: {bg_mood['primary_style']} ({bg_mood['category']})
따뜻함: {bg_mood['warmth_score']:.1%}

Top 3 추천 상품:
1. {products[0]['name'][:50]} (점수: {products[0]['match_score']:.3f})
2. {products[1]['name'][:50]} (점수: {products[1]['match_score']:.3f})
3. {products[2]['name'][:50]} (점수: {products[2]['match_score']:.3f})

매칭 품질:
- 평균 매칭 점수: {np.mean(total_scores):.3f}
- 색상 유사도가 가장 높음: 평균 {np.mean(color_scores):.3f}
- 물리적 유사도가 매우 높음: 평균 {np.mean(physics_scores):.3f}
- 스타일 유사도: 평균 {np.mean(style_scores):.3f}

알고리즘 특징:
- 스타일 매칭(50%)이 가장 큰 영향
- 색상 조화(30%)가 두 번째 중요
- 물리적 특성(20%)으로 최종 조정
""")

print("\n✅ 분석 완료!")

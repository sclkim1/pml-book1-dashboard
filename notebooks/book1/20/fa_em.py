"""Reference implementation of EM for factor analysis (FA) and PPCA.

PML book 1, section 20.2. The model is

    p(z) = N(0, I),   p(x | z) = N(W z + mu, Psi),   so   p(x) = N(mu, W W^T + Psi),

with a diagonal noise covariance Psi (FA) or Psi = sigma^2 I (PPCA).
This is the standalone version of fa_em_demo.ipynb; it needs only NumPy
(scikit-learn is used by main() for a check if it is installed).

Run `python fa_em.py` to fit both models to synthetic data, check them against
their reference solutions and print the comparison; add `--plot` for the figures.
Import it to reuse the pieces:

    from fa_em import fa_em
    res = fa_em(X, L=2)                  # FA
    res = fa_em(X, L=2, isotropic=True)  # PPCA
"""

import argparse
from dataclasses import dataclass

import numpy as np


@dataclass
class FAResult:
    mu: np.ndarray  # [D], mean
    W: np.ndarray  # [D, L], loadings (identified only up to a rotation of z)
    psi: np.ndarray  # [D], noise variances (all equal to sigma^2 for PPCA)
    lls: np.ndarray  # log-likelihood after each iteration
    converged: bool


def make_data(N=500, psi=(0.05, 0.1, 0.2, 0.5, 1.0, 2.0), L=2, seed=0):
    """Samples N points from an FA model with noise variances psi; returns X and the true parameters."""
    rng = np.random.default_rng(seed)
    psi = np.asarray(psi, dtype=float)
    D = len(psi)
    W = rng.standard_normal((D, L))
    mu = rng.standard_normal(D)
    Z = rng.standard_normal((N, L))
    X = Z @ W.T + mu + rng.standard_normal((N, D)) * np.sqrt(psi)
    return X, {"W": W, "psi": psi, "mu": mu}


def loglik(X, mu, W, psi):
    """sum_n log N(x_n | mu, W W^T + diag(psi))."""
    N, D = X.shape
    C = W @ W.T + np.diag(psi)
    chol = np.linalg.cholesky(C)
    R = np.linalg.solve(chol, (X - mu).T)  # whitened residuals, [D, N]
    logdet = 2 * np.log(np.diag(chol)).sum()
    return -0.5 * (N * (D * np.log(2 * np.pi) + logdet) + (R**2).sum())


def e_step(Xc, W, psi):
    """Posterior p(z_n | x_n) = N(m_n, G) for centered data Xc.

    Returns M (row n is m_n, [N, L]), G ([L, L], the same for every n) and
    sum_n E[z_n z_n^T] = N G + M^T M.
    """
    N = Xc.shape[0]
    L = W.shape[1]
    WtPinv = W.T / psi  # W^T Psi^{-1}, [L, D]
    G = np.linalg.inv(np.eye(L) + WtPinv @ W)
    M = Xc @ (G @ WtPinv).T
    Ezz = N * G + M.T @ M
    return M, G, Ezz


def m_step(Xc, S, M, Ezz, isotropic=False):
    """Updates W, then Psi = diag(S - W (1/N) sum_n m_n x_n^T); PPCA averages it into sigma^2."""
    N, D = Xc.shape
    W = (Xc.T @ M) @ np.linalg.inv(Ezz)
    psi = np.diag(S - W @ (M.T @ Xc) / N).copy()
    if isotropic:
        psi = np.full(D, psi.mean())
    return W, psi


def fa_em(X, L, isotropic=False, n_iter=5000, tol=1e-8, seed=0):
    """EM for factor analysis; isotropic=True ties the noise variances (PPCA).

    Stops when the relative change in log-likelihood falls below tol.
    """
    N, D = X.shape
    mu = X.mean(axis=0)  # the MLE of mu, so EM only has to fit W and Psi
    Xc = X - mu
    S = Xc.T @ Xc / N
    rng = np.random.default_rng(seed)
    W = rng.standard_normal((D, L))
    psi = np.diag(S).copy()
    if isotropic:
        psi = np.full(D, psi.mean())
    lls = []
    converged = False
    for it in range(n_iter):
        M, _, Ezz = e_step(Xc, W, psi)
        W, psi = m_step(Xc, S, M, Ezz, isotropic)
        lls.append(loglik(X, mu, W, psi))
        if it > 0 and abs(lls[-1] - lls[-2]) < tol * abs(lls[-2]):
            converged = True
            break
    return FAResult(mu, W, psi, np.array(lls), converged)


def ppca_closed_form(X, L):
    """Tipping and Bishop's MLE: sigma^2 is the mean of the D - L smallest eigenvalues of S,
    W = U_L (Lambda_L - sigma^2 I)^{1/2}."""
    mu = X.mean(axis=0)
    evals, evecs = np.linalg.eigh(np.cov(X.T, bias=True))
    evals, evecs = evals[::-1], evecs[:, ::-1]
    sigma2 = evals[L:].mean()
    W = evecs[:, :L] * np.sqrt(evals[:L] - sigma2)
    return mu, W, sigma2


def max_cov_diff(W1, W2):
    """W is identified only up to a rotation of z, so loadings are compared through W W^T."""
    return np.abs(W1 @ W1.T - W2 @ W2.T).max()


def plot(fa, ppca, truth):
    import matplotlib.pyplot as plt

    colors = ["#2a78d6", "#eb6834"]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    ax = axes[0]
    for res, name, color in [(fa, "FA", colors[0]), (ppca, "PPCA", colors[1])]:
        ax.plot(np.arange(1, len(res.lls) + 1), res.lls, color=color, lw=2, label=name)
    ax.set_xscale("log")
    ax.set_xlabel("iteration")
    ax.set_ylabel("log-likelihood")
    ax.legend()

    ax = axes[1]
    D = len(fa.psi)
    x = np.arange(D)
    w = 0.27
    for i, (vals, name, color) in enumerate(
        [(truth["psi"], r"true $\Psi$", "0.6"), (fa.psi, "FA", colors[0]), (ppca.psi, r"PPCA $\sigma^2$", colors[1])]
    ):
        ax.bar(x + (i - 1) * w, vals, w * 0.9, color=color, label=name)
    ax.set_xticks(x)
    ax.set_xticklabels([f"$x_{j + 1}$" for j in range(D)])
    ax.set_ylabel("noise variance")
    ax.legend()
    fig.tight_layout()
    plt.show()


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--N", type=int, default=500)
    parser.add_argument("--L", type=int, default=2)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--plot", action="store_true", help="show the log-likelihood and noise-variance plots")
    args = parser.parse_args()

    X, truth = make_data(N=args.N, L=args.L, seed=args.seed)
    N, D = X.shape
    print(f"data: N={N}, D={D}, L={args.L}, true noise variances {truth['psi']}")

    fa = fa_em(X, args.L)
    ppca = fa_em(X, args.L, isotropic=True)
    for name, res in [("FA", fa), ("PPCA", ppca)]:
        assert np.all(np.diff(res.lls) > -1e-6), f"{name} EM log-likelihood decreased"
        status = "converged" if res.converged else "not converged"
        print(f"{name} EM: {len(res.lls)} iterations ({status}), log-likelihood {res.lls[-1]:.3f}")

    print("\nchecks")
    try:
        from sklearn.decomposition import FactorAnalysis
    except ModuleNotFoundError:
        print("  FA vs sklearn: skipped (scikit-learn not installed)")
    else:
        sk = FactorAnalysis(n_components=args.L, tol=1e-8, max_iter=10000).fit(X)
        print(f"  FA vs sklearn: log-likelihood {sk.score(X) * N:.3f}, "
              f"max |W W^T diff| {max_cov_diff(fa.W, sk.components_.T):.4f}")
    mu_cf, W_cf, sigma2_cf = ppca_closed_form(X, args.L)
    print(f"  PPCA vs closed form: sigma^2 {sigma2_cf:.4f} (EM {ppca.psi[0]:.4f}), "
          f"log-likelihood {loglik(X, mu_cf, W_cf, np.full(D, sigma2_cf)):.3f}, "
          f"max |W W^T diff| {max_cov_diff(ppca.W, W_cf):.4f}")
    print(f"  FA vs truth: max |W W^T diff| {max_cov_diff(fa.W, truth['W']):.4f}")

    print("\nFA vs PPCA")
    print(f"  log-likelihood gain of FA: {fa.lls[-1] - ppca.lls[-1]:.1f}")
    print("  noise variance   true     FA   PPCA")
    for j in range(D):
        print(f"  x_{j + 1}           {truth['psi'][j]:6.3f} {fa.psi[j]:6.3f} {ppca.psi[j]:6.3f}")

    if args.plot:
        plot(fa, ppca, truth)


if __name__ == "__main__":
    main()

/* solve-lbl.js — GENERATED, do not edit by hand.
   Produced by: node tools/cube/solve.js --write
   One continuous solve of one scrambled cube: every figure below is a stage of
   the same solve, and the moves of a stage take its figure to the next one.
   The camera of each figure looks at the face the step is about. */
const SOLVE_LBL = {
  "scramble": "R U F' L2 D B' R2 U' F2 D2 L B2 U2 R' F D' L2 B U2 L2 F U",
  "states": {
    "cross": [
      {
        "label": "شروع: مکعب به‌هم‌ریخته",
        "alg": "R U F' L2 D B' R2 U' F2 D2 L B2 U2 R' F D' L2 B U2 L2 F U",
        "next": "F2 B' R' L'",
        "view": "default"
      },
      {
        "label": "دیزی: چهار سفید دور مرکز زرد",
        "alg": "R U F' L2 D B' R2 U' F2 D2 L B2 U2 R' F D' L2 B U2 L2 F U F2 B' R' L'",
        "next": "R2 U B2 L2 U F2",
        "view": "top"
      },
      {
        "label": "صلیب سفید: هر لبه بالای مرکز هم‌رنگش",
        "alg": "R U F' L2 D B' R2 U' F2 D2 L B2 U2 R' F D' L2 B U2 L2 F U F2 B' R' L' R2 U B2 L2 U F2",
        "next": null,
        "view": "bottom"
      }
    ],
    "corners1": [
      {
        "label": "قبل از این گام: صلیب آماده است",
        "alg": "R U F' L2 D B' R2 U' F2 D2 L B2 U2 R' F D' L2 B U2 L2 F U F2 B' R' L' R2 U B2 L2 U F2",
        "next": " U F' U' F R' U2 R B' U B L' U L",
        "view": "bottom"
      },
      {
        "label": "بعد از این گام: لایه اول کامل",
        "alg": "R U F' L2 D B' R2 U' F2 D2 L B2 U2 R' F D' L2 B U2 L2 F U F2 B' R' L' R2 U B2 L2 U F2 U F' U' F R' U2 R B' U B L' U L",
        "next": null,
        "view": "bottom"
      }
    ],
    "layer2": [
      {
        "label": "قبل از این گام: لایه اول کامل است",
        "alg": "R U F' L2 D B' R2 U' F2 D2 L B2 U2 R' F D' L2 B U2 L2 F U F2 B' R' L' R2 U B2 L2 U F2 U F' U' F R' U2 R B' U B L' U L",
        "next": "U F U' F' U' L' U L U2 R U' R' U' F' U F U' R' U R U B U' B' U' L U' L' U' B' U B F U' F' U' L' U L",
        "view": "bottom"
      },
      {
        "label": "بعد از این گام: دو لایه پایین کامل",
        "alg": "R U F' L2 D B' R2 U' F2 D2 L B2 U2 R' F D' L2 B U2 L2 F U F2 B' R' L' R2 U B2 L2 U F2 U F' U' F R' U2 R B' U B L' U L U F U' F' U' L' U L U2 R U' R' U' F' U F U' R' U R U B U' B' U' L U' L' U' B' U B F U' F' U' L' U L",
        "next": null,
        "view": "bottom"
      }
    ],
    "yellowCross": [
      {
        "label": "قبل از این گام: روی زرد بی‌شکل",
        "alg": "R U F' L2 D B' R2 U' F2 D2 L B2 U2 R' F D' L2 B U2 L2 F U F2 B' R' L' R2 U B2 L2 U F2 U F' U' F R' U2 R B' U B L' U L U F U' F' U' L' U L U2 R U' R' U' F' U F U' R' U R U B U' B' U' L U' L' U' B' U B F U' F' U' L' U L",
        "next": "F R U R' U' R U R' U' F'",
        "view": "top"
      },
      {
        "label": "بعد از این گام: صلیب زرد",
        "alg": "R U F' L2 D B' R2 U' F2 D2 L B2 U2 R' F D' L2 B U2 L2 F U F2 B' R' L' R2 U B2 L2 U F2 U F' U' F R' U2 R B' U B L' U L U F U' F' U' L' U L U2 R U' R' U' F' U F U' R' U R U B U' B' U' L U' L' U' B' U B F U' F' U' L' U L F R U R' U' R U R' U' F'",
        "next": null,
        "view": "top"
      }
    ],
    "yellowOrient": [
      {
        "label": "قبل از این گام: صلیب زرد، گوشه‌ها برگشته",
        "alg": "R U F' L2 D B' R2 U' F2 D2 L B2 U2 R' F D' L2 B U2 L2 F U F2 B' R' L' R2 U B2 L2 U F2 U F' U' F R' U2 R B' U B L' U L U F U' F' U' L' U L U2 R U' R' U' F' U F U' R' U R U B U' B' U' L U' L' U' B' U B F U' F' U' L' U L F R U R' U' R U R' U' F'",
        "next": "U' R U R' U R U2 R' U2 R U2 R' U' R U' R'",
        "view": "top"
      },
      {
        "label": "بعد از این گام: تمام وجه زرد یک‌رنگ",
        "alg": "R U F' L2 D B' R2 U' F2 D2 L B2 U2 R' F D' L2 B U2 L2 F U F2 B' R' L' R2 U B2 L2 U F2 U F' U' F R' U2 R B' U B L' U L U F U' F' U' L' U L U2 R U' R' U' F' U F U' R' U R U B U' B' U' L U' L' U' B' U B F U' F' U' L' U L F R U R' U' R U R' U' F' U' R U R' U R U2 R' U2 R U2 R' U' R U' R'",
        "next": null,
        "view": "top"
      }
    ],
    "yellowCorners": [
      {
        "label": "قبل از این گام: وجه زرد کامل، گوشه‌ها جابه‌جا",
        "alg": "R U F' L2 D B' R2 U' F2 D2 L B2 U2 R' F D' L2 B U2 L2 F U F2 B' R' L' R2 U B2 L2 U F2 U F' U' F R' U2 R B' U B L' U L U F U' F' U' L' U L U2 R U' R' U' F' U F U' R' U R U B U' B' U' L U' L' U' B' U B F U' F' U' L' U L F R U R' U' R U R' U' F' U' R U R' U R U2 R' U2 R U2 R' U' R U' R'",
        "next": "R' F R' B2 R F' R' B2 R2 U R2 B2 R F R' B2 R F' R",
        "view": "top"
      },
      {
        "label": "بعد از این گام: گوشه‌ها سر جای خودشان",
        "alg": "R U F' L2 D B' R2 U' F2 D2 L B2 U2 R' F D' L2 B U2 L2 F U F2 B' R' L' R2 U B2 L2 U F2 U F' U' F R' U2 R B' U B L' U L U F U' F' U' L' U L U2 R U' R' U' F' U F U' R' U R U B U' B' U' L U' L' U' B' U B F U' F' U' L' U L F R U R' U' R U R' U' F' U' R U R' U R U2 R' U2 R U2 R' U' R U' R2 F R' B2 R F' R' B2 R2 U R2 B2 R F R' B2 R F' R",
        "next": null,
        "view": "top"
      }
    ],
    "yellowEdges": [
      {
        "label": "قبل از این گام: فقط جای سه لبه مانده",
        "alg": "R U F' L2 D B' R2 U' F2 D2 L B2 U2 R' F D' L2 B U2 L2 F U F2 B' R' L' R2 U B2 L2 U F2 U F' U' F R' U2 R B' U B L' U L U F U' F' U' L' U L U2 R U' R' U' F' U F U' R' U R U B U' B' U' L U' L' U' B' U B F U' F' U' L' U L F R U R' U' R U R' U' F' U' R U R' U R U2 R' U2 R U2 R' U' R U' R2 F R' B2 R F' R' B2 R2 U R2 B2 R F R' B2 R F' R",
        "next": "M2 U' M U2 M' U' M2",
        "view": "top"
      },
      {
        "label": "بعد از این گام: مکعب حل شد",
        "alg": "R U F' L2 D B' R2 U' F2 D2 L B2 U2 R' F D' L2 B U2 L2 F U F2 B' R' L' R2 U B2 L2 U F2 U F' U' F R' U2 R B' U B L' U L U F U' F' U' L' U L U2 R U' R' U' F' U F U' R' U R U B U' B' U' L U' L' U' B' U B F U' F' U' L' U L F R U R' U' R U R' U' F' U' R U R' U R U2 R' U2 R U2 R' U' R U' R' R' F R' B2 R F' R' B2 R2 U R2 B2 R F R' B2 R F' R M2 U' M U2 M' U' M2",
        "next": null,
        "view": "top",
        "solved": true
      }
    ]
  },
  "order": [
    "cross",
    "corners1",
    "layer2",
    "yellowCross",
    "yellowOrient",
    "yellowCorners",
    "yellowEdges"
  ],
  "labels": {
    "cross": "صلیب سفید",
    "corners1": "گوشه‌های لایه اول",
    "layer2": "لبه‌های لایه دوم",
    "yellowCross": "صلیب زرد",
    "yellowOrient": "وجه زرد کامل",
    "yellowCorners": "جای گوشه‌های زرد",
    "yellowEdges": "جای لبه‌های زرد"
  },
  "turned": [
    "cross",
    "corners1",
    "layer2"
  ],
  "turn": ""
};

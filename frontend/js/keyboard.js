
document.addEventListener("DOMContentLoaded", () => {
    // Elemen-elemen DOM
    const keyboard = document.getElementById("keyboard");
    const inputFields = document.querySelectorAll(
        'input[type="password"]'
    );
    let currentInput = null; // Menyimpan input yang sedang aktif

    // Layout keyboard
    const layout = [
        ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "Backspace"],
        ["q", "w", "e", "r", "t", "y", "u", "i", "o", "p"],
        ["CapsLock", "a", "s", "d", "f", "g", "h", "j", "k", "l", "Enter"],
        ["Shift", "z", "x", "c", "v", "b", "n", "m", ",", ".", "?"],
        ["space"],
    ];

    // State untuk tombol modifier
    let shiftActive = false;
    let capsLockActive = false;

    // Pemetaan karakter ke versi Shift-nya
    const shiftMap = {
        1: "!",
        2: "@",
        3: "#",
        4: "$",
        5: "%",
        6: "^",
        7: "&",
        8: "*",
        9: "(",
        0: ")",
        ",": "<",
        ".": ">",
        "?": "/",
        // Tambahkan lebih banyak sesuai kebutuhan
    };

    // Fungsi untuk membuat tombol keyboard
    function createKey(char) {
        const key = document.createElement("button");
        key.classList.add("key");

        // Atur atribut dan kelas untuk tombol khusus
        switch (char) {
            case "space":
                key.classList.add("extra-wide");
                key.dataset.value = " ";
                key.innerHTML = "&nbsp;"; // Gunakan spasi HTML untuk visibilitas
                break;
            case "Backspace":
                key.classList.add("wide");
                key.dataset.value = "Backspace";
                key.textContent = "⌫";
                break;
            case "Enter":
                key.classList.add("wide");
                key.dataset.value = "Enter";
                key.textContent = "↵";
                break;
            case "Shift":
                key.classList.add("wide");
                key.dataset.value = "Shift";
                key.textContent = "⇧";
                break;
            case "CapsLock":
                key.classList.add("wide");
                key.dataset.value = "CapsLock";
                key.textContent = "⇪";
                break;
            default:
                key.dataset.value = char;
                key.textContent = char;
                key.classList.add("key-letter");
        }
        return key;
    }

    // Fungsi untuk merender seluruh keyboard
    function renderKeyboard() {
        keyboard.innerHTML = ""; // Kosongkan keyboard sebelum merender ulang
        layout.forEach((row) => {
            const rowElement = document.createElement("div");
            rowElement.classList.add("keyboard-row");
            row.forEach((key) => {
                const keyElement = createKey(key);
                rowElement.appendChild(keyElement);
            });
            keyboard.appendChild(rowElement);
        });
        updateKeyCase(); // Perbarui huruf besar/kecil setelah render
    }

    // Fungsi untuk memperbarui huruf besar/kecil pada tombol
    function updateKeyCase() {
        const letterKeys = keyboard.querySelectorAll(".key-letter");
        letterKeys.forEach((key) => {
            const char = key.dataset.value;
            // Logika yang benar untuk Caps Lock dan Shift
            if (
                (capsLockActive && !shiftActive) ||
                (!capsLockActive && shiftActive)
            ) {
                key.textContent = char.toUpperCase();
            } else {
                key.textContent = char.toLowerCase();
            }
        });

        // Perbarui tombol non-huruf berdasarkan status Shift
        const allKeys = keyboard.querySelectorAll(".key");
        allKeys.forEach((key) => {
            const char = key.dataset.value;
            if (
                shiftActive &&
                !key.classList.contains("key-letter") &&
                !key.classList.contains("wide") &&
                !key.classList.contains("extra-wide")
            ) {
                // Tampilkan karakter Shift jika Shift aktif
                if (shiftMap[char]) {
                    key.textContent = shiftMap[char];
                }
            } else if (
                !key.classList.contains("key-letter") &&
                !key.classList.contains("wide") &&
                !key.classList.contains("extra-wide")
            ) {
                // Kembalikan teks asli jika Shift tidak aktif
                key.textContent = char;
            }
        });
    }

    // Fungsi untuk menangani klik pada tombol
    function handleKeyPress(event) {
        const key = event.target;
        const keyValue = key.dataset.value;
        const value = currentInput.value;

        switch (keyValue) {
            case "Backspace":
                currentInput.value = value.slice(0, -1);
                break;
            case "Enter":
                // Sembunyikan keyboard dan pindah fokus
                keyboard.classList.remove("active");
                currentInput.blur();

                break;
            case "CapsLock":
                capsLockActive = !capsLockActive;
                key.classList.toggle("active");
                updateKeyCase();
                break;
            case "Shift":
                shiftActive = !shiftActive;
                key.classList.toggle("active");
                updateKeyCase();
                break;
            case " ":
                currentInput.value += " ";
                break;
            default:
                // Tentukan karakter yang akan ditambahkan berdasarkan status Caps Lock dan Shift
                let charToAdd = keyValue;

                // Periksa apakah ini adalah huruf
                if (keyValue.length === 1 && keyValue.match(/[a-z]/i)) {
                    // Logika yang benar untuk Caps Lock dan Shift
                    if (
                        (capsLockActive && !shiftActive) ||
                        (!capsLockActive && shiftActive)
                    ) {
                        charToAdd = keyValue.toUpperCase();
                    } else {
                        charToAdd = keyValue.toLowerCase();
                    }
                } else if (shiftActive) {
                    // Untuk tombol non-huruf, gunakan nilai Shift dari peta
                    charToAdd = shiftMap[keyValue] || keyValue;
                }

                currentInput.value += charToAdd;

                // Nonaktifkan Shift setelah mengetik satu karakter
                // Ini adalah perilaku standar untuk keyboard fisik
                // Jika Anda ingin Shift tetap aktif hingga ditekan lagi, komentar baris berikut
                if (shiftActive) {
                    shiftActive = false;
                    keyboard
                        .querySelector('[data-value="Shift"]')
                        .classList.remove("active");
                    updateKeyCase();
                }
        }
        // Letakkan kursor di akhir input
        currentInput.focus();
    }

    // Event listener untuk setiap input field
    inputFields.forEach((input) => {
        input.addEventListener("focus", () => {
            currentInput = input;
            keyboard.classList.add("active");
        });
    });

    // Event listener untuk menutup keyboard jika klik di luar area keyboard/input
    document.addEventListener("click", (event) => {
        if (
            !keyboard.contains(event.target) &&
            event.target.tagName !== "INPUT"
        ) {
            keyboard.classList.remove("active");
            currentInput = null;
        }
    });

    // Event delegation untuk menangani klik pada tombol
    keyboard.addEventListener("click", handleKeyPress);

    // Inisialisasi keyboard saat halaman dimuat
    renderKeyboard();
});

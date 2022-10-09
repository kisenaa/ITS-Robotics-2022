// NAMA		: Johannes Daniswara Pratama
// NRP		: 5025221276
// Jurusan	: Teknik Informatika

#include <iostream>

#include <cmath>

#define GRAVITASI 10 //10 m/s^2
#define START_PENGUKURAN 1 //pengukuran dimulai dari 1 meter
#define SUDUT 45 //sudut elevasi tembakan

float mencari_V0(float vt, float speed_loss) {
    /* Tulis fungsi mencari v0 kalian disini */
    float V0 = vt - speed_loss;
    return V0;

}

float speed_dgn_loss(float x1) {
    /* tulis fungsi hitung_loss kalian disini */
    float inputs = 0;
    if (x1 >= 2 && x1 <= 11) {
        inputs = 1;
    } else if (x1 >= 14 && x1 <= 23) {
        inputs = 3;
    } else if (x1 >= 26 && x1 <= 30) {
        inputs = 5;
    }

    return inputs;

}

int main() {
    float loss;
    float input, V0;
    int jarak;

    std::cin >> input;

    loss = speed_dgn_loss(input);
    V0 = mencari_V0(input, loss);

    // Calculating distance (int)
    jarak = powf(V0, 2) * sin(2 * SUDUT * 3.14159 / 180) / GRAVITASI;

    // Calculating V Tangensial for int jarak
    double z = sqrt(jarak * GRAVITASI / (sin(2 * SUDUT * 3.14159 / 180))) + loss;

    std::cout << jarak << " " << z << std::endl;
    return 0;
}

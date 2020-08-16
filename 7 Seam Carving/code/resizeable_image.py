import imagematrix

class ResizeableImage(imagematrix.ImageMatrix):
    def best_seam(self):
        dp, energy, parent = {}, {}, {}
        for i in range(self.width):
            for j in range(self.height):
                energy[i, j] = self.energy(i, j)
        for i in range(self.width):
            dp[i, 0] = energy[i, 0]

        for j in range(1, self.height):
            for i in range(self.width):
                dp[i, j] = energy[i, j] + dp[i, j - 1]
                parent[i, j] = (i, j - 1)
                if i != 0 and dp[i, j] > energy[i, j] + dp[i - 1, j - 1]:
                    dp[i, j] = energy[i, j] + dp[i - 1, j - 1]
                    parent[i, j] = (i - 1, j - 1)
                if i != self.width - 1 and dp[i, j] > energy[i, j] + dp[i + 1, j - 1]:
                    dp[i, j] = energy[i, j] + dp[i + 1, j - 1]
                    parent[i, j] = (i + 1, j - 1)

        best_value = dp[0, self.height - 1]
        index = 0
        for i in range(1, self.width):
            if dp[i, self.height - 1] < best_value:
                best_value = dp[i, self.height - 1]
                index = i

        seam = [(index, self.height - 1)]
        for i in range(self.height - 1):
            seam.append(parent[seam[-1]])
        return seam

    def remove_best_seam(self):
        self.remove_seam(self.best_seam())

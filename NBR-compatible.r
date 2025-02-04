# Load necessary libraries ---------------------------
library(NBR)
library(lattice)
library(parallel)

# Set directory paths -------------------------------
data_dir <- "data/ALL"
subject_csv <- "data/subject-id.csv"

# List all CSV files in the directory ----------------
file_list <- list.files(data_dir, pattern = "*.csv", full.names = TRUE)

# Load matrices and filter based on dimensions ------
matrix_list <- lapply(file_list, function(file) {
  mat <- as.matrix(read.csv(file, header = FALSE, skip = 1))  # Skip headers
  if (all(dim(mat) == c(148, 148))) {
    return(mat)
  } else {
    warning(sprintf("Skipping %s (dimensions: %s)", file, paste(dim(mat), collapse = "x")))
    return(NULL)
  }
})

# Remove NULL matrices ------------------------------
matrix_list <- Filter(Negate(is.null), matrix_list)
num_subjects <- length(matrix_list)

# Initialize 3D array for matrices -------------------
cmx <- array(NA, dim = c(148, 148, num_subjects))
for (i in seq_along(matrix_list)) {
  cmx[,,i] <- matrix_list[[i]]
}

cat("Loaded", num_subjects, "distance matrices.\n")

# Read Phenotypic Data ------------------------------
subject_data <- read.csv(subject_csv)

# Ensure subject count matches ----------------------
stopifnot(num_subjects == nrow(subject_data))

# Create phenotype dataframe ------------------------
phen <- data.frame(
  GROUP = subject_data$GROUP,  
  sex = ifelse(subject_data$sex == 1, 0, 1),
  age = subject_data$age,
  TIV = subject_data$TIV
)

# Compute Average Connectivity ---------------------
avg_mx <- apply(cmx, 1:2, mean, na.rm = TRUE)
flim <- max(abs(avg_mx), na.rm = TRUE)

# Plot Average Connectivity ------------------------
levelplot(avg_mx, main = "Average Connectivity Matrix",
          ylab = "ROI", xlab = "ROI",
          at = seq(-flim, flim, length.out = 100),
          col.regions = colorRampPalette(c("green", "white", "red")))

# Save processed data ------------------------------
saveRDS(list(cmx = cmx, phen = phen), file = "results/processed_data.rds")

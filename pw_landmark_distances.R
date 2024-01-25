pw_landmark_distances <- function(file) {
  # Calculated landmarks distances
  
  library(readr)
  library(jsonlite)

  # read json file datas
  data <- fromJSON(file, flatten = TRUE)
  
  # if landmarkc show values ...
  if (length(data$markups) > 0) {
    # create a list to stock datas
    coordinates_list <- list()
    
    # loop to access each coordinates of each label (landmarks)
    for (point in data$markups$controlPoints) {
      for (i in seq_along(point$label)) {
        x <- point$position[[i]][1]
        y <- point$position[[i]][2]
        z <- point$position[[i]][3]
        label <- point$label[i]
        
        # Stocke coordinates
        coordinates_list[[label]] <- c(x, y, z)
        
        # show coordinates
        cat("ID:", label, "\tCoordinates (x, y, z):", x, y, z, "\n")
      }
    }
    
    # convert list to df 
    coordinates_df <- as.data.frame(do.call(rbind, coordinates_list))
    colnames(coordinates_df) <- c("X", "Y", "Z")
    
    # add colone for ID
    coordinates_df$ID <- names(coordinates_list)
  } else {
    cat("Aucun point de repère trouvé dans le fichier.\n")
  }
  
  
  ## distances 
  
  # function based on euclidean distances to compute 3d distances
  distance_3d <- function(x1, y1, z1, x2, y2, z2) {
    return(sqrt((x1 - x2)^2 + (y1 - y2)^2 + (z1 - z2)^2))
  }
  
  # create matrix filled with zero 
  dist_matrix <- matrix(0, nrow = nrow(coordinates_df), ncol = nrow(coordinates_df))
  
  # loop using the function
  for (i in 1:(nrow(coordinates_df) - 1)) {
    for (j in (i + 1):nrow(coordinates_df)) {
      dist_matrix[i, j] <- sqrt((coordinates_df$X[i] - coordinates_df$X[j])^2 +
                                  (coordinates_df$Y[i] - coordinates_df$Y[j])^2 +
                                  (coordinates_df$Z[i] - coordinates_df$Z[j])^2)
      dist_matrix[j, i] <- dist_matrix[i, j]  # La matrice est symétrique
    }
  }
  
  # matrix to df
  dist_df <- as.data.frame(dist_matrix)
  colnames(dist_df) <- coordinates_df$ID
  rownames(dist_df) <- coordinates_df$ID
  print(dist_df)
}

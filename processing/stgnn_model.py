import torch
import torch.nn as nn


class SpatialGraphConv(nn.Module):
    """
    Simple GraphSAGE-style graph convolution.

    Each node combines:
    - its own features
    - mean features from neighboring nodes
    """

    def __init__(
        self,
        in_features,
        out_features
    ):
        super().__init__()

        self.self_linear = nn.Linear(
            in_features,
            out_features
        )

        self.neighbor_linear = nn.Linear(
            in_features,
            out_features
        )

        self.activation = nn.ReLU()

    def forward(
        self,
        x,
        adjacency
    ):
        """
        x:
            [batch, nodes, features]

        adjacency:
            [nodes, nodes]
        """

        # Add self loops
        A = adjacency + torch.eye(
            adjacency.size(0),
            device=adjacency.device
        )

        # Normalize by node degree
        degree = A.sum(
            dim=1,
            keepdim=True
        )

        A_norm = A / degree.clamp(
            min=1.0
        )

        # Neighbor aggregation
        neighbor_features = torch.matmul(
            A_norm,
            x
        )

        out = (
            self.self_linear(x)
            +
            self.neighbor_linear(
                neighbor_features
            )
        )

        return self.activation(out)


class STGNN(nn.Module):

    def __init__(
        self,
        num_nodes,
        input_features,
        spatial_hidden=32,
        temporal_hidden=32,
        forecast_days=7
    ):
        super().__init__()

        self.num_nodes = num_nodes
        self.forecast_days = forecast_days

        # Spatial encoder
        self.graph_conv = SpatialGraphConv(
            input_features,
            spatial_hidden
        )

        # Temporal encoder
        self.gru = nn.GRU(
            input_size=spatial_hidden,
            hidden_size=temporal_hidden,
            num_layers=1,
            batch_first=True
        )

        # Prediction head
        self.output_layer = nn.Linear(
            temporal_hidden,
            forecast_days
        )

    def forward(
        self,
        x,
        adjacency
    ):
        """
        x:
            [batch, time, nodes, features]

        adjacency:
            [nodes, nodes]

        returns:
            [batch, forecast_days, nodes]
        """

        batch_size = x.size(0)
        time_steps = x.size(1)

        spatial_outputs = []

        # Apply graph convolution independently
        # to each daily graph snapshot.
        for t in range(time_steps):

            daily_x = x[:, t, :, :]

            spatial_x = self.graph_conv(
                daily_x,
                adjacency
            )

            spatial_outputs.append(
                spatial_x
            )

        # [time, batch, nodes, hidden]
        spatial_outputs = torch.stack(
            spatial_outputs,
            dim=1
        )

        # Rearrange so each ward has its own
        # temporal sequence.
        #
        # [batch, time, nodes, hidden]
        # ->
        # [batch * nodes, time, hidden]
        spatial_outputs = spatial_outputs.permute(
            0, 2, 1, 3
        )

        spatial_outputs = spatial_outputs.reshape(
            batch_size * self.num_nodes,
            time_steps,
            -1
        )

        # GRU
        temporal_output, _ = self.gru(
            spatial_outputs
        )

        # Last observed timestep
        last_output = temporal_output[:, -1, :]

        predictions = self.output_layer(
            last_output
        )

        # [batch * nodes, forecast_days]
        # ->
        # [batch, forecast_days, nodes]

        predictions = predictions.reshape(
            batch_size,
            self.num_nodes,
            self.forecast_days
        )

        predictions = predictions.permute(
            0,
            2,
            1
        )

        return predictions

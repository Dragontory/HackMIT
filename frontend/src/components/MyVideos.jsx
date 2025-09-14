import React, { useEffect, useState } from "react";

const MyVideos = () => {
    const [videos, setVideos] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchVideos = async () => {
            const token = localStorage.getItem("access_token");
            if (!token) return;

            const response = await fetch("http://127.0.0.1:8000/my_videos", {
                headers: { Authorization: `Bearer ${token}` },
            });

            if (response.ok) {
                const data = await response.json();
                setVideos(data);
            } else {
                console.log("Unauthorized");
            }

            setLoading(false);
        };

        fetchVideos();
    }, []);

    return (
        <div>
            <h2>My Videos</h2>
            {loading ? (
                <p>Loading...</p>
            ) : (
                <ul>
                    {videos.map((video) => (
                        <li key={video.id}>{video.title}</li>
                    ))}
                </ul>
            )}
        </div>
    );
};


export default MyVideos;
